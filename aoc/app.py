# app.py (updated)
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import clickhouse_connect
from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np
from functools import reduce
import shutil
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# 临时数据目录（按站点子目录）
TMP_DIR = "tmp_data"
os.makedirs(TMP_DIR, exist_ok=True)

# -----------------------
# ClickHouse 配置
# -----------------------
clickhouse_config = {
    'host': 'bytehouse.huoshan.accurain.cn',
    'port': 80,
    'username': 'accuraindev',
    'password': '2P%#9N8qVSb@sQ',
    'database': 'dev',
    'compression': 'gzip'
}
client = clickhouse_connect.get_client(**clickhouse_config)

# -----------------------
# 数据表配置
# -----------------------
TABLE_CONFIG = {
    'pwv': {
        'table': 'ods_pwv_external',
        'fields': ['data_time', 'device', 'pwv', 'data_type']
    },
    'weather': {
        'table': 'ods_hws_external',
        'fields': ['data_time', 'device', 'ta', 'pa', 'ua', 'data_type']
    },
    'rain': {
        'table': 'ods_raingauge_external',
        'fields': ['data_time', 'device', 'rainfall', 'data_type']
    }
}

# 默认来源优先级(可手动调整顺序)
DEFAULT_SOURCE_PRIORITY = ['deviced', 'cros', 'ec', 'era5']


# -----------------------
# 首页
# -----------------------
@app.route('/')
def index():
    return render_template('index.html')


# -----------------------
# 数据上传接口（前端 upload 使用）
# 将文件保存到 tmp_data/<device>/ 原始文件名
# 返回 tmp_file 名称和解析出的起止时间
# -----------------------
@app.route('/upload_data', methods=['POST'])
def upload_data():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未检测到文件'}), 400
        file = request.files['file']
        dtype = request.form.get('type')  # pwv/weather/rain
        device = request.form.get('device') or request.form.get('station_id')
        if not device:
            return jsonify({'error': '设备/站点参数缺失'}), 400

        filename = secure_filename(file.filename)
        site_dir = os.path.join(TMP_DIR, device)
        os.makedirs(site_dir, exist_ok=True)
        save_path = os.path.join(site_dir, filename)
        file.save(save_path)

        # 解析 CSV 获取时间范围
        start_time = None
        end_time = None
        try:
            df = pd.read_csv(save_path, encoding='utf-8-sig', nrows=10000)
            # 优先使用 'data_time' 列，其次尝试 'date'/'time' 列
            time_col = None
            for col in df.columns:
                if col.lower() in ['data_time', 'date', 'time'] or '时间' in col:
                    time_col = col
                    break
                # 解析完整文件，以获取最小/最大时间
                df_full = pd.read_csv(save_path, encoding='utf-8-sig', usecols=[time_col])
                dt = pd.to_datetime(df_full[time_col], errors='coerce')
                if dt.notna().any():
                    start_time = dt.min().strftime('%Y/%m/%d %H:%M:%S')
                    end_time = dt.max().strftime('%Y/%m/%d %H:%M:%S')
        except Exception:
            pass

        return jsonify({
            'status': 'success',
            'tmp_file': filename,
            'start_time': start_time,
            'end_time': end_time
        })
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


# -----------------------
#单类型下载接口(保留)
# -----------------------
@app.route('/download_data', methods=['POST'])
def download_data():
    data = request.json
    data_type = data.get('type')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    device = data.get('device') or data.get('station_id')

    if not all([data_type, start_time, end_time, device]):
        return jsonify({'error': '参数缺失'}), 400

    config = TABLE_CONFIG.get(data_type)
    if not config:
        return jsonify({'error': '数据类型错误'}), 400

    table = config['table']
    fields = config['fields']

    try:
        start_dt = datetime.fromisoformat(start_time) - timedelta(hours=8)
        end_dt = datetime.fromisoformat(end_time) - timedelta(hours=8)
    except Exception:
        return jsonify({'error': '时间格式错误，应为 ISO 格式，例如 2025-10-21T00:00:00'}), 400

    merged_data = {}
    for source in DEFAULT_SOURCE_PRIORITY:
        query_fields = ', '.join(fields)
        query = f"""
            SELECT {query_fields}
            FROM {table}
            WHERE device = '{device}'
              AND data_time >= toDateTime('{start_dt.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
              AND data_time <= toDateTime('{end_dt.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
              AND LOWER(data_type) = '{source.lower()}'
            ORDER BY data_time ASC
            LIMIT 50000
        """
        try:
            result = client.query(query)
            rows = [dict(zip(result.column_names, row)) for row in result.result_rows]
            for row in rows:
                t = row['data_time']
                t_str = t.strftime("%Y-%m-%d %H:%M:%S") if isinstance(t, datetime) else str(t)
                if t_str not in merged_data:
                    if isinstance(t, datetime):
                        row['data_time'] = (t + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                    merged_data[t_str] = row
        except Exception as e:
            return jsonify({'error': f'查询失败: {str(e)}'}), 500

    if not merged_data:
        return jsonify({'error': '所有数据源均无可用数据'}), 404

    data_list = [merged_data[k] for k in sorted(merged_data.keys())]

    # 保存
    site_dir = os.path.join(TMP_DIR, device)
    os.makedirs(site_dir, exist_ok=True)
    start_str = start_dt.strftime("%Y-%m-%d_%H-%M-%S")
    end_str = end_dt.strftime("%Y-%m-%d_%H-%M-%S")
    tmp_file_name = f"{data_type}_{start_str}_{end_str}.csv"
    tmp_file = os.path.join(site_dir, tmp_file_name)
    pd.DataFrame(data_list).to_csv(tmp_file, index=False, encoding='utf-8-sig')

    return jsonify({
        'count': len(data_list),
        'data': data_list[:1000],
        'tmp_file': tmp_file_name
    })


# -----------------------
# 批量下载接口（保留）
# -----------------------
@app.route('/batch_download', methods=['POST'])
def batch_download():
    try:
        payload = request.json
        types = payload.get('types') or []
        start_time = payload.get('start_time')
        end_time = payload.get('end_time')
        device = payload.get('device') or payload.get('station_id')
        priority = payload.get('priority') or DEFAULT_SOURCE_PRIORITY

        if not all([types, start_time, end_time, device]):
            return jsonify({'error': '参数缺失(types/start_time/end_time/device)'}), 400

        # 优先级转换为小写
        priority = [str(p).lower() for p in priority if p]

        results = []
        for data_type in types:
            config = TABLE_CONFIG.get(data_type)
            if not config:
                results.append({'type': data_type, 'count': -1, 'error': '未知数据类型'})
                continue

            table = config['table']
            fields = config['fields']

            try:
                start_dt = datetime.fromisoformat(start_time) - timedelta(hours=8)
                end_dt = datetime.fromisoformat(end_time) - timedelta(hours=8)
            except Exception:
                results.append({'type': data_type, 'count': -1, 'error': '时间格式错误'})
                continue

            merged_data = {}
            # 按优先级顺序查询各数据源，依次填充时间戳
            for source in priority:
                query_fields = ', '.join(fields)
                query = f"""
                    SELECT {query_fields}
                    FROM {table}
                    WHERE device = '{device}'
                      AND data_time >= toDateTime('{start_dt.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
                      AND data_time <= toDateTime('{end_dt.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
                      AND LOWER(data_type) = '{source}'
                    ORDER BY data_time ASC
                    LIMIT 100000
                """
                try:
                    result = client.query(query)
                    rows = [dict(zip(result.column_names, row)) for row in result.result_rows]
                    for row in rows:
                        t = row['data_time']
                        t_str = t.strftime("%Y-%m-%d %H:%M:%S") if isinstance(t, datetime) else str(t)
                        
                        if t_str in merged_data:
                            continue
                        if isinstance(t, datetime):
                            row['data_time'] = (t + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                        merged_data[t_str] = row
                except Exception as e:
                    results.append({'type': data_type, 'count': -1, 'error': f'查询失败: {str(e)}'})
                    merged_data = {}
                    break

            if not merged_data:
                results.append({'type': data_type, 'count': 0, 'tmp_file': None})
                continue

            data_list = [merged_data[k] for k in sorted(merged_data.keys())]

            # 保存到站点文件夹（按时间命名，避免覆盖）
            site_dir = os.path.join(TMP_DIR, device)
            os.makedirs(site_dir, exist_ok=True)
            start_str = start_dt.strftime("%Y-%m-%d_%H-%M-%S")
            end_str = end_dt.strftime("%Y-%m-%d_%H-%M-%S")
            tmp_file_name = f"{data_type}_{start_str}_{end_str}.csv"
            tmp_file = os.path.join(site_dir, tmp_file_name)
            pd.DataFrame(data_list).to_csv(tmp_file, index=False, encoding='utf-8-sig')

            results.append({
                'type': data_type,
                'count': len(data_list),
                'tmp_file': tmp_file_name
            })

        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'error': f'批量下载失败: {str(e)}'}, 500)


# -----------------------
# 合并数据接口（支持传入 site）
# -----------------------
@app.route('/merge_datasets', methods=['POST'])
def merge_datasets():
    try:
        payload = request.get_json(silent=True) or {}
        target_site = payload.get('site', None)

        site_dirs = [d for d in os.listdir(TMP_DIR) if os.path.isdir(os.path.join(TMP_DIR, d))]
        if target_site:
            if target_site not in site_dirs:
                return jsonify({'error': f'站点 {target_site} 不存在或无上传数据'}), 400
            site_dirs = [target_site]

        if not site_dirs:
            return jsonify({'error': '没有可用站点数据'}), 400

        results = []
        for site in site_dirs:
            site_path = os.path.join(TMP_DIR, site)
            csv_files = [os.path.join(site_path, f) for f in os.listdir(site_path) if f.endswith('.csv') and not f.startswith('dataset_')]
            if len(csv_files) < 1:
                # 没有数据文件跳过
                continue

            standardized_dfs = []
            for f in csv_files:
                try:
                    df = pd.read_csv(f, encoding='utf-8-sig')
                except Exception:
                    continue

                # 标准化时间列名为 'date'
                time_col_candidates = ['data_time', 'date', 'time']
                time_col = None
                for col in df.columns:
                    if col.lower() in time_col_candidates or '时间' in col:
                        time_col = col
                        break
                if not time_col:
                    continue
                df = df.rename(columns={time_col: 'date'})
                # parse date and set index
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna(subset=['date'])
                df = df.set_index('date')

                # 列名映射（把不同文件的列映为统一标准列）
                col_map = {
                    'ta': 't2m', 't2m': 't2m',
                    'pa': 'sp', 'sp': 'sp',
                    'ua': 'rh', 'rh': 'rh',
                    'pwv': 'pwv',
                    'rainfall': 'tp', 'tp': 'tp'
                }
                df_cols = {}
                for c in df.columns:
                    ck = c.strip()
                    if ck in col_map:
                        df_cols[ck] = col_map[ck]

                # 构造标准化 df，包含需要的列
                std_df = pd.DataFrame(index=df.index)
                for orig_col, std_col in df_cols.items():
                    std_df[std_col] = pd.to_numeric(df[orig_col], errors='coerce').round(3)
                # ensure all target cols exist
                for col in ['t2m', 'sp', 'rh', 'pwv', 'tp']:
                    if col not in std_df.columns:
                        std_df[col] = np.nan

                standardized_dfs.append(std_df[['t2m', 'sp', 'rh', 'pwv', 'tp']])

            if not standardized_dfs:
                continue

            # 按顺序 combine_first（先出现的优先）
            merged = standardized_dfs[0].copy()
            for other in standardized_dfs[1:]:
                merged = merged.combine_first(other)

            merged = merged.sort_index().reset_index()
            merged = merged.rename(columns={'index': 'date'})

            # 把 date 格式化为字符串
            merged['date'] = merged['date'].dt.strftime('%Y/%m/%d %H:%M:%S')

            # 保存合并文件
            now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            dataset_name = f"dataset_{now_str}.csv"
            merged_path = os.path.join(site_path, dataset_name)
            merged.to_csv(merged_path, index=False, encoding='utf-8-sig')

            # 计算时间范围
            try:
                first_date = pd.to_datetime(merged['date'], errors='coerce').min()
                last_date = pd.to_datetime(merged['date'], errors='coerce').max()
                if pd.notna(first_date) and pd.notna(last_date):
                    time_range = f"{first_date.strftime('%Y/%m/%d %H:%M:%S')} ~ {last_date.strftime('%Y/%m/%d %H:%M:%S')}"
                else:
                    time_range = "未知"
            except Exception:
                time_range = "未知"

            results.append({
                'site_id': site,
                'dataset': dataset_name,
                'time_range': time_range
            })

        if not results:
            return jsonify({'error': '没有站点合并成功'}), 400
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'error': f'合并失败: {str(e)}'}), 500


# -----------------------
# 获取所有站点或指定站点的数据集列表
# -----------------------
@app.route('/get_datasets')
def get_datasets():
    site = request.args.get('site')

    if not site:
        # 返回站点列表
        sites = [d for d in os.listdir(TMP_DIR) if os.path.isdir(os.path.join(TMP_DIR, d))]
        out = [{'site_id': s} for s in sites]
        return jsonify(out)

    site_dir = os.path.join(TMP_DIR, site)
    if not os.path.exists(site_dir):
        return jsonify({"datasets": []})

    files = [f for f in os.listdir(site_dir) if f.endswith('.csv')]
    datasets = []
    for file in files:
        path = os.path.join(site_dir, file)
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"读取 {file} 出错: {e}")
            continue

        # 自动匹配时间列
        time_col = None
        for col in df.columns:
            if col.lower() in ['time', 'date'] or '时间' in col:
                time_col = col
                break

        if not time_col:
            datasets.append({
                "name": file,
                "site": site,
                "site_name": f"站点{site}",
                "start_time": None,
                "end_time": None,
                "created_at": time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(os.path.getctime(path)))
            })
            continue

        try:
            start_time = str(pd.to_datetime(df[time_col], errors='coerce').min())
            end_time = str(pd.to_datetime(df[time_col], errors='coerce').max())
        except Exception:
            start_time = None
            end_time = None

        datasets.append({
            "name": file,
            "site": site,
            "site_name": f"站点{site}",
            "start_time": start_time,
            "end_time": end_time,
            "created_at": time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(os.path.getctime(path)))
        })

    return jsonify({"datasets": datasets})


# -----------------------
# 临时文件访问（预览） & 下载 & 删除
# -----------------------
@app.route('/tmp_data/<path:filename>/<site>')
def serve_tmp_data(filename, site):
    site_path = os.path.join(TMP_DIR, site)
    return send_from_directory(site_path, filename)


@app.route('/delete_dataset/<filename>/<site>', methods=['DELETE'])
def delete_dataset(filename, site):
    path = os.path.join(TMP_DIR, site, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'status': 'success', 'message': f'{filename} 已删除'})
    else:
        return jsonify({'status': 'error', 'message': f'{filename} 不存在'})


@app.route('/tmp_data_preview/<filename>/<site>')
def tmp_data_preview(filename, site):
    site_path = os.path.join(TMP_DIR, site)
    path = os.path.join(site_path, filename)
    if not os.path.exists(path):
        return jsonify({'error': '文件不存在'}), 404
    try:
        df = pd.read_csv(path)

        def clean_columns(col_base):
            for suffix in ['', '_x', '_y']:
                if col_base + suffix in df.columns:
                    return df[col_base + suffix]
            
            for c in df.columns:
                if c.lower() in [col_base, col_base.lower()]:
                    return df[c]
            return pd.Series([None]*len(df))
        
        clean_df = pd.DataFrame({
            'date': clean_columns('date') if 'date' in df.columns else clean_columns('data_time'),
            't2m': clean_columns('t2m'),
            'sp': clean_columns('sp'),
            'rh': clean_columns('rh'),
            'pwv': clean_columns('pwv'),
            'tp': clean_columns('tp')
        })

        clean_df['date'] = pd.to_datetime(clean_df['date'], errors='coerce').dt.strftime('%Y/%m/%d %H:%M:%S')
        clean_df = clean_df.where(pd.notnull(clean_df), None)
        preview_rows = clean_df.head(100).to_dict(orient='records')
        return jsonify({'rows': preview_rows})
    except Exception as e:
        return jsonify({'error': f'获取详情失败: {str(e)}'}), 500


# -----------------------
# 启动 Flask
# -----------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
