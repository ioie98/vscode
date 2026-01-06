# app.py
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import clickhouse_connect
from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np
from functools import reduce
import shutil

app = Flask(__name__)
CORS(app)

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

SOURCE_PRIORITY = ['era5', 'ec', 'cros', 'deviced']

# -----------------------
# 临时数据存储（按站点）
# -----------------------
TMP_DIR = "tmp_data"
os.makedirs(TMP_DIR, exist_ok=True)

# -----------------------
# 首页
# -----------------------
@app.route('/')
def index():
    return render_template('index.html')

# -----------------------
# 下载数据到站点文件夹
# -----------------------
# -----------------------
# 下载数据到站点文件夹
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
    for source in SOURCE_PRIORITY[::-1]:
        query_fields = ', '.join(fields)
        query = f"""
            SELECT {query_fields}
            FROM {table}
            WHERE device = '{device}'
              AND data_time >= toDateTime('{start_dt.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
              AND data_time <= toDateTime('{end_dt.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
              AND LOWER(data_type) = '{source.lower()}'
            ORDER BY data_time ASC
            LIMIT 5000
        """
        try:
            result = client.query(query)
            rows = [dict(zip(result.column_names, row)) for row in result.result_rows]
            for row in rows:
                t = row['data_time']
                t_str = t.strftime("%Y-%m-%d %H:%M:%S") if isinstance(t, datetime) else str(t)
                if t_str not in merged_data or SOURCE_PRIORITY.index(source) < SOURCE_PRIORITY.index(merged_data[t_str]['data_type']):
                    if isinstance(t, datetime):
                        row['data_time'] = (t + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                    merged_data[t_str] = row
        except Exception as e:
            return jsonify({'error': f'查询失败: {str(e)}'}), 500

    if not merged_data:
        return jsonify({'error': '所有数据源均无可用数据'}), 404

    data_list = [merged_data[k] for k in sorted(merged_data.keys())]

    # 保存到站点文件夹（按时间命名，避免覆盖）
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
# 合并数据接口
# -----------------------
@app.route('/merge_datasets', methods=['POST'])
def merge_datasets():
    try:
        site_dirs = [d for d in os.listdir(TMP_DIR) if os.path.isdir(os.path.join(TMP_DIR, d))]
        if not site_dirs:
            return jsonify({'error': '没有可用站点数据'}), 400

        results = []
        for site in site_dirs:
            site_path = os.path.join(TMP_DIR, site)
            csv_files = [os.path.join(site_path, f) for f in os.listdir(site_path) if f.endswith('.csv') and not f.startswith('dataset_')]
            if len(csv_files) < 3:
                continue  # 数据不足，跳过

            dfs = []
            for f in csv_files:
                df = pd.read_csv(f)
                valid_cols = [c for c in ['data_time', 'ta', 'pa', 'ua', 'pwv', 'rainfall'] if c in df.columns]
                dfs.append(df[valid_cols])
            
            merged = reduce(lambda left, right: pd.merge(left, right, on='data_time', how='outer'), dfs)
            merged = merged.sort_values(by='data_time').reset_index(drop=True)

            col_map = {
                'data_time': 'date',
                'ta': 't2m',
                'pa': 'sp',
                'ua': 'rh',
                'pwv': 'pwv',
                'rainfall': 'tp'
            }
            for k, v in col_map.items():
                if k in merged.columns:
                    merged.rename(columns={k: v}, inplace=True)
                else:
                    merged[v] = np.nan

            merged = merged[['date', 't2m', 'sp', 'rh', 'pwv', 'tp']]
            for col in ['t2m', 'sp', 'rh', 'pwv', 'tp']:
                merged[col] = pd.to_numeric(merged[col], errors='coerce').round(3)

            # 保存合并文件
            existing = [f for f in os.listdir(site_path) if f.startswith('dataset_')]
            dataset_name = f"dataset_{len(existing)+1}.csv"
            merged_path = os.path.join(site_path, dataset_name)
            merged.to_csv(merged_path, index=False, encoding='utf-8-sig')

            first_date = pd.to_datetime(merged['date'], errors='coerce').min().strftime('%Y/%m/%d %H:%M:%S')
            last_date = pd.to_datetime(merged['date'], errors='coerce').max().strftime('%Y/%m/%d %H:%M:%S')
            time_range = f"{first_date} ~ {last_date}"

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
# 获取所有站点数据状态
# -----------------------
@app.route('/get_datasets')
def get_datasets():
    all_data = []
    for site in os.listdir(TMP_DIR):
        site_path = os.path.join(TMP_DIR, site)
        if os.path.isdir(site_path):
            files = os.listdir(site_path)
            pwv = 'pwv.csv' in files
            weather = 'weather.csv' in files or '气象.csv' in files
            rain = 'rain.csv' in files or '雨量筒.csv' in files
            merged_files = [f for f in files if f.startswith('dataset_') and f.endswith('.csv')]
            
            all_data.append({
                'site_id': site,
                'pwv': pwv,
                'weather': weather,
                'rain': rain,
                'merged': merged_files
            })
    return jsonify(all_data)

# -----------------------
# 临时文件访问
# -----------------------
@app.route('/tmp_data/<path:filename>/<site>')
def serve_tmp_data(filename, site):
    site_path = os.path.join(TMP_DIR, site)
    return send_from_directory(site_path, filename)


# 删除数据集
@app.route('/delete_dataset/<filename>/<site>', methods=['DELETE'])
def delete_dataset(filename, site):
    path = os.path.join(TMP_DIR, site, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'status': 'success', 'message': f'{filename} 已删除'})
    else:
        return jsonify({'status': 'error', 'message': f'{filename} 不存在'})


# -----------------------
# 数据预览接口
# -----------------------
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
            return pd.Series([None]*len(df))
        
        clean_df = pd.DataFrame({
            'date': clean_columns('date'),
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
