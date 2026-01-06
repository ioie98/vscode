from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import clickhouse_connect
from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np
import shutil
import time
from werkzeug.utils import secure_filename
import traceback
import re
from urllib.parse import unquote
import json

app = Flask(__name__)
CORS(app)

# 临时数据目录
TMP_DIR = "tmp_data"
# 全局进度字典（保留以防以后扩展）
progress_dict = {}
os.makedirs(TMP_DIR, exist_ok=True)


# ClickHouse 配置（保留你原来的配置）
clickhouse_config = {
    'host': 'bytehouse.huoshan.accurain.cn',
    'port': 80,
    'username': 'accuraindev',
    'password': '2P%#9N8qVSb@sQ',
    'database': 'dev',
    'compression': 'gzip'
}
client = clickhouse_connect.get_client(**clickhouse_config)


# 数据表配置
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



# 首页
@app.route('/')
def index():
    return render_template('index.html')



# 数据上传接口
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
            df_head = pd.read_csv(save_path, encoding='utf-8-sig', nrows=10000)
            time_col = None
            for col in df_head.columns:
                if col.lower() in ['data_time', 'date', 'time'] or '时间' in col:
                    time_col = col
                    break
            if time_col:
                df_full_time = pd.read_csv(save_path, encoding='utf-8-sig', usecols=[time_col])
                dt = pd.to_datetime(df_full_time[time_col], errors='coerce')
                if dt.notna().any():
                    start_time = dt.min().strftime('%Y/%m/%d %H:%M:%S')
                    end_time = dt.max().strftime('%Y/%m/%d %H:%M:%S')
        except Exception:
            pass

        inserted_count = 0
        # 将数据写入 ClickHouse
        if dtype in TABLE_CONFIG:
            try:
                df = pd.read_csv(save_path, encoding='utf-8-sig')
                # 寻找时间列
                time_col = None
                for col in df.columns:
                    if col.lower() in ['data_time', 'date', 'time'] or '时间' in col:
                        time_col = col
                        break
                if time_col is None:
                    return jsonify({
                        'status': 'success',
                        'tmp_file': filename,
                        'start_time': start_time,
                        'end_time': end_time,
                        'inserted_count': 0,
                        'error': '上传文件无时间列，未写入数据库'
                    })

                # 标准化列名以便提取需要字段
                cfg = TABLE_CONFIG[dtype]
                required_fields = cfg['fields']
                insert_df = pd.DataFrame()

                # data_time 列规范为 datetime
                insert_df['data_time'] = pd.to_datetime(df[time_col], errors='coerce')

                # 如果文件已有 device 列则用文件列，否则使用上传的 device 参数
                if 'device' in df.columns:
                    insert_df['device'] = df['device'].astype(str)
                else:
                    insert_df['device'] = device

                # 其它字段按配置映射
                col_map_basic = {
                    'pwv': ['pwv', 'PWV', 'PwV'],
                    'ta': ['ta','t2m','T','temp','temperature'],
                    'pa': ['pa','sp','pressure'],
                    'ua': ['ua','rh','humidity'],
                    'rainfall': ['rain','rainfall','tp','precip']
                }

                # 映射其它字段
                for f in required_fields:
                    if f not in ['data_time', 'device', 'data_type']:
                        insert_df[f] = np.nan

                for col in df.columns:
                    lc = col.strip().lower()
                    for target_field, candidates in col_map_basic.items():
                        if lc in [c.lower() for c in candidates]:
                            if target_field in insert_df.columns:
                                insert_df[target_field] = pd.to_numeric(df[col], errors='coerce')

                if 'data_type' in df.columns:
                    insert_df['data_type'] = df['data_type'].astype(str)
                else:
                    insert_df['data_type'] = 'uploaded'

                # 丢弃无效时间行
                insert_df = insert_df.dropna(subset=['data_time'])
                if insert_df.empty:
                    inserted_count = 0
                else:
                    # 去重
                    min_t = insert_df['data_time'].min()
                    max_t = insert_df['data_time'].max()
                    table = cfg['table']

                    # 查询已有时间
                    try:
                        q = f"""
                            SELECT data_time FROM {table}
                            WHERE device = '{device}'
                              AND data_time >= toDateTime('{(min_t - timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
                              AND data_time <= toDateTime('{(max_t + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
                        """
                        res = client.query(q)
                        existing_times = set()
                        for row in res.result_rows:
                            t = row[0]
                            if isinstance(t, datetime):
                                existing_times.add(t.strftime("%Y-%m-%d %H:%M:%S"))
                            else:
                                existing_times.add(str(t))
                    except Exception as e:
                        existing_times = set()
                        print("Warning: 查询已有时间失败，允许全部写入。错误：", e)
                    
                    def is_new_row(ts):
                        # compare by string in "%Y-%m-%d %H:%M:%S"
                        s = pd.to_datetime(ts).strftime("%Y-%m-%d %H:%M:%S")
                        return s not in existing_times

                    to_insert_df = insert_df[insert_df['data_time'].apply(is_new_row)].copy()
                    if not to_insert_df.empty:
                        to_insert_df['data_time'] = to_insert_df['data_time'].dt.strftime("%Y-%m-%d %H:%M:%S")
                        records = []
                        for _, row in to_insert_df.iterrows():
                            rec = {}
                            for f in cfg['fields']:
                                if f in row:
                                    rec[f] = None if (pd.isna(row[f])) else row[f]
                                else:
                                    if f == 'data_time':
                                        rec[f] = row.get('data_time')
                                    elif f == 'device':
                                        rec[f] = row.get('device')
                                    elif f == 'data_type':
                                        rec[f] = row.get('data_type', 'uploaded')
                                    else:
                                        rec[f] = None
                            records.append(rec)
                        try:
                            client.insert(cfg['table'], records, column_names=cfg['fields'])
                            inserted_count = len(records)
                        except Exception as e:
                            print("ClickHouse 插入失败：", e)
                            inserted_count = 0
                    else:
                        inserted_count = 0
            except Exception as e:
                print("上传写入数据库异常：", e)
                traceback.print_exc()
        else:
            inserted_count = 0

        return jsonify({
            'status': 'success',
            'tmp_file': filename,
            'start_time': start_time,
            'end_time': end_time,
            'inserted_count': inserted_count
        })
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({'error': f'上传失败: {str(e)}', 'trace': traceback_str}), 500



# 单类型下载接口(保留)
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
            return jsonify({'error': f'查询失败: {str(e)}'}, 500)

    if not merged_data:
        return jsonify({'error': '所有数据源均无可用数据'}), 404

    data_list = [merged_data[k] for k in sorted(merged_data.keys())]

    # 保存到根目录
    site_dir = os.path.join(TMP_DIR, device)
    os.makedirs(site_dir, exist_ok=True)
    start_str = start_dt.strftime("%Y-%m-%d_%H-%M-%S")
    end_str = end_dt.strftime("%Y-%m-%d_%H-%M-%S")

    tmp_file_name = f"{data_type}_{start_str}_{end_str}.csv"
    tmp_file = os.path.join(site_dir, tmp_file_name)
    pd.DataFrame(data_list).to_csv(tmp_file, index=False, encoding='utf-8-sig')

    # 返回相对路径
    rel_path = os.path.join(tmp_file_name)

    return jsonify({
        'count': len(data_list),
        'data': data_list[:1000],
        'tmp_file': rel_path
    })


# 单站点单类型下载
def _download_single_type_for_device(device, data_type, start_time, end_time, priority_list):
    config = TABLE_CONFIG.get(data_type)
    if not config:
        return {'type': data_type, 'count': -1, 'error': '未知数据类型'}

    table = config['table']
    fields = config['fields']

    try:
        #北京时间 →  UTC
        start_local = datetime.fromisoformat(start_time)
        end_local = datetime.fromisoformat(end_time)

        start_utc = start_local - timedelta(hours=8)
        end_utc = end_local - timedelta(hours=8)
    except Exception:
        return {'type': data_type, 'count': -1, 'error': '时间格式错误'}

    merged_data = {}

    for source in priority_list:
        query_fields = ', '.join(fields)
        query = f"""
            SELECT {query_fields}
            FROM {table}
            WHERE device = '{device}'
              AND data_time >= toDateTime('{start_utc.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
              AND data_time <= toDateTime('{end_utc.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
              AND LOWER(data_type) = '{source}'
            ORDER BY data_time ASC
            LIMIT 100000
        """

        try:
            result = client.query(query)
            rows = [dict(zip(result.column_names, row)) for row in result.result_rows]

            for row in rows:
                t = row['data_time']
                # 转北京时间
                if isinstance(t, datetime):
                    local_t = t + timedelta(hours=8)
                    row['data_time'] = local_t.strftime("%Y-%m-%d %H:%M:%S")
                    t_str = row['data_time']
                else:
                    t_str = str(t)

                if t_str not in merged_data:
                    merged_data[t_str] = row
        except Exception as e:
            return {'type': data_type, 'count': -1, 'error': f'查询失败: {str(e)}'}

    if not merged_data:
        return {'type': data_type, 'count': 0, 'tmp_file': None}

    data_list = [merged_data[k] for k in sorted(merged_data.keys())]
    # 保存到站点根目录
    site_dir = os.path.join(TMP_DIR, device)
    os.makedirs(site_dir, exist_ok=True)

    start_str = start_local.strftime("%Y-%m-%d_%H-%M-%S")
    end_str = end_local.strftime("%Y-%m-%d_%H-%M-%S")

    tmp_file_name = f"{data_type}_{start_str}_{end_str}.csv"
    tmp_file = os.path.join(site_dir, tmp_file_name)

    try:
        pd.DataFrame(data_list).to_csv(tmp_file, index=False, encoding='utf-8-sig')
    except Exception as e:
        return {'type': data_type, 'count': -1, 'error': f'保存失败: {str(e)}'}

    rel_path = os.path.join(tmp_file_name)
    return {'type': data_type, 'count': len(data_list), 'tmp_file': rel_path}


# 批量下载接口
@app.route('/batch_download', methods=['POST'])
def batch_download():
    try:
        payload = request.json or {}
        types = payload.get('types') or []
        start_time = payload.get('start_time')
        end_time = payload.get('end_time')
        devices = payload.get('devices') or payload.get('devices_list') or None
        single_device = payload.get('device') or payload.get('station_id') or None
        priority = payload.get('priority') or DEFAULT_SOURCE_PRIORITY
        mode = (payload.get('mode') or 'train').lower()  # train / pred

        # 支持单设备参数
        if not devices and single_device:
            devices = [single_device]

        if not all([types, start_time, end_time, devices]):
            return jsonify({'error': '参数缺失(types/start_time/end_time/devices)'}), 400

        # 处理优先级列表
        priority_list = [str(p).lower() for p in priority if p]

        overall_results = []
        # 遍历设备
        for device in devices:
            device_result = {'device': device, 'results': []}
            try:
                for data_type in types:
                    res = _download_single_type_for_device(device, data_type, start_time, end_time, priority_list)
                    device_result['results'].append(res)
                overall_results.append(device_result)
            except Exception as e:
                device_result['results'].append({'type': 'internal', 'count': -1, 'error': f'内部异常: {str(e)}'})
                overall_results.append(device_result)

        # 下载完成后自动合并
        try:
            merged = merge_datasets_inner(devices, mode)
        except Exception as e:
            merged = {'status': 'error', 'message': f'合并异常: {str(e)}', 'trace': traceback.format_exc()}

        return jsonify({'status': 'success', 'details': overall_results, 'merged': merged})
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({'error': f'批量下载失败: {str(e)}', 'trace': traceback_str}), 500


# 接收站点列表并合并
def merge_datasets_inner(sites, mode='train'):
    results = []
    for site in sites:
        site = site.strip()
        site_path = os.path.join(TMP_DIR, site)
        if not os.path.exists(site_path):
            results.append({'site_id': site, 'error': '站点无数据可合并'})
            continue

        # 合并非 dataset 文件
        csv_files = []
        # 根目录的 csv
        for f in os.listdir(site_path):
            full = os.path.join(site_path, f)
            if os.path.isfile(full) and f.lower().endswith('.csv') and not re.match(r'^dataset[-_]', f, re.I):
                csv_files.append(full)
        # 子目录的 csv
        for d in os.listdir(site_path):
            sub = os.path.join(site_path, d)
            if os.path.isdir(sub):
                for f in os.listdir(sub):
                    full = os.path.join(sub, f)
                    if os.path.isfile(full) and f.lower().endswith('.csv') and not re.match(r'^dataset[-_]', f, re.I):
                        csv_files.append(full)

        if not csv_files:
            existing = []
            mode_dir = os.path.join(site_path, mode)
            if os.path.exists(mode_dir):
                for fn in os.listdir(mode_dir):
                    if fn.lower().endswith('.csv') and re.match(r'^dataset[-_]', fn, re.I):
                        existing.append({'site_id': site, 'sub_dir': mode, 'dataset': fn})
            if existing:
                results.append({'site_id': site, 'sub_dir': mode, 'dataset_list': [e['dataset'] for e in existing]})
            else:
                results.append({'site_id': site, 'error': '站点无可合并的 CSV 文件'})
            continue

        standardized_dfs = []
        for fpath in csv_files:
            try:
                df = pd.read_csv(fpath, encoding='utf-8-sig')
            except Exception:
                try:
                    df = pd.read_csv(fpath)
                except Exception:
                    continue

            # 统一时间列名为 date
            time_col_candidates = ['data_time', 'date', 'time']
            time_col = None
            for col in df.columns:
                if col.lower() in time_col_candidates or '时间' in col:
                    time_col = col
                    break
            if not time_col:
                continue

            df = df.rename(columns={time_col: 'date'})
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
            df = df.set_index('date')

            # 列映射（标准列名：t2m, sp, rh, pwv, tp）
            col_map = {
                'ta': 't2m', 't2m': 't2m',
                'pa': 'sp', 'sp': 'sp',
                'ua': 'rh', 'rh': 'rh',
                'pwv': 'pwv',
                'rainfall': 'tp', 'tp': 'tp'
            }

            std_cols = {}
            for c in df.columns:
                ck = c.strip().lower()
                if ck in col_map:
                    std_cols[c] = col_map[ck]

            std_df = pd.DataFrame(index=df.index)
            for orig_col, std_col in std_cols.items():
                try:
                    std_df[std_col] = pd.to_numeric(df[orig_col], errors='coerce').round(3)
                except Exception:
                    std_df[std_col] = np.nan

            # 保证所有列存在
            for col in ['t2m', 'sp', 'rh', 'pwv', 'tp']:
                if col not in std_df.columns:
                    std_df[col] = np.nan

            standardized_dfs.append(std_df[['t2m', 'sp', 'rh', 'pwv', 'tp']])

        if not standardized_dfs:
            results.append({'site_id': site, 'error': '没有可标准化的 CSV 数据'})
            continue

        # 合并
        merged = standardized_dfs[0].copy()
        for other in standardized_dfs[1:]:
            merged = merged.combine_first(other)

        merged = merged.sort_index().reset_index()
        merged = merged.rename(columns={'index': 'date'})
        merged['date'] = merged['date'].dt.strftime('%Y/%m/%d %H:%M:%S')

        # 生成 dataset 文件
        now_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        dataset_name = f"dataset-{now_str}.csv"
        mode_dir = os.path.join(site_path, mode)
        os.makedirs(mode_dir, exist_ok=True)
        merged_path = os.path.join(mode_dir, dataset_name)
        try:
            merged.to_csv(merged_path, index=False, encoding='utf-8-sig')
        except Exception as e:
            results.append({'site_id': site, 'error': f'保存合并文件失败: {str(e)}'})
            continue

        # 生成时间范围
        try:
            first_date = pd.to_datetime(merged['date'], errors='coerce').min()
            last_date = pd.to_datetime(merged['date'], errors='coerce').max()
            time_range = f"{first_date.strftime('%Y/%m/%d %H:%M:%S')} ~ {last_date.strftime('%Y/%m/%d %H:%M:%S')}" \
                if pd.notna(first_date) and pd.notna(last_date) else "未知"
        except Exception:
            time_range = "未知"

        # 删除原始 csv （只删除用于合并的中间 csv）
        try:
            for fpath in csv_files:
                try:
                    if os.path.exists(fpath):
                        os.remove(fpath)
                except Exception:
                    pass

            # 删除站点根目录下的空子目录
            for d in os.listdir(site_path):
                sub = os.path.join(site_path, d)
                if os.path.isdir(sub):
                    try:
                        if not os.listdir(sub):
                            os.rmdir(sub)
                    except Exception:
                        pass
        except Exception:
            pass

        results.append({
            'site_id': site,
            'sub_dir': mode,
            'dataset': dataset_name,
            'time_range': time_range
        })

    if not results:
        return {'status': 'success', 'message': '所有目录均已合并或无可合并项'}
    return {'status': 'success', 'results': results}


# 合并数据接口
@app.route('/merge_datasets', methods=['POST'])
def merge_datasets():
    try:
        payload = request.get_json(silent=True) or {}
        selected_sites = payload.get('sites', [])
        mode = (payload.get('mode') or 'train').lower()
        if not selected_sites:
            return jsonify({'success': False, 'msg': '请选择站点'}), 400

        merged = merge_datasets_inner(selected_sites, mode)
        return jsonify({'success': True, 'msg': '合并完成', 'merged': merged})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'msg': str(e), 'trace': traceback.format_exc()}), 500




# 获取指定站点的数据集列表（返回 train + pred ）
@app.route('/get_datasets')
def get_datasets_route():
    site = request.args.get('site')

    if not site:
        # 返回站点列表（site id 列表）
        sites = [d for d in os.listdir(TMP_DIR) if os.path.isdir(os.path.join(TMP_DIR, d))]
        return jsonify([{'site_id': s} for s in sites])

    site = site.strip()
    site_dir = os.path.join(TMP_DIR, site)
    if not os.path.exists(site_dir):
        return jsonify({"train": [], "pred": []})

    def list_mode_files(mode):
        out = []
        mode_dir = os.path.join(site_dir, mode)
        if os.path.exists(mode_dir):
            for file in os.listdir(mode_dir):
                if file.endswith('.csv') and re.match(r'^dataset[-_]', file, re.I):
                    path = os.path.join(mode_dir, file)
                    # 读取 CSV 获取时间范围
                    try:
                        df = pd.read_csv(path)
                        time_col = next((c for c in df.columns if c.lower() in ['time','date'] or '时间' in c), None)
                        if time_col:
                            start_time = str(pd.to_datetime(df[time_col], errors='coerce').min())
                            end_time = str(pd.to_datetime(df[time_col], errors='coerce').max())
                        else:
                            start_time = None
                            end_time = None
                    except:
                        start_time = None
                        end_time = None

                    out.append({
                        "sub_dir": mode,
                        "name": file,
                        "site": site,
                        "site_name": f"站点{site}",
                        "start_time": start_time,
                        "end_time": end_time,
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(path))),
                        "path": os.path.join(mode, file)
                    })
        return out

    train_files = list_mode_files("train")
    pred_files = list_mode_files("pred")

    # 按文件创建时间倒序
    train_files.sort(key=lambda x: os.path.getctime(os.path.join(site_dir, x['path'])), reverse=True)
    pred_files.sort(key=lambda x: os.path.getctime(os.path.join(site_dir, x['path'])), reverse=True)

    return jsonify({"train": train_files, "pred": pred_files})


# 获取文件行（详情预览）
@app.route('/get_file_rows')
def get_file_rows():
    site = request.args.get('site')
    mode = request.args.get('mode')
    file = request.args.get('file')

    if not all([site, mode, file]):
        return jsonify({'error': '参数缺失(site/mode/file)'}), 400

    if '/' in file or '\\' in file:
        file = os.path.basename(file)

    file_path = os.path.join(TMP_DIR, site, mode, file)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    try:
        df = pd.read_csv(file_path)
        def pick_col(col_base):
            for suffix in ['', '_x', '_y']:
                if col_base + suffix in df.columns:
                    return df[col_base + suffix]
            for c in df.columns:
                if c.lower() in [col_base, col_base.lower()]:
                    return df[c]
            return pd.Series([None]*len(df))

        clean_df = pd.DataFrame({
            'date': pick_col('date') if 'date' in df.columns else pick_col('data_time'),
            't2m': pick_col('t2m'),
            'sp': pick_col('sp'),
            'rh': pick_col('rh'),
            'pwv': pick_col('pwv'),
            'tp': pick_col('tp')
        })
        clean_df['date'] = pd.to_datetime(clean_df['date'], errors='coerce').dt.strftime('%Y/%m/%d %H:%M:%S')
        clean_df = clean_df.where(pd.notnull(clean_df), None)
        rows = clean_df.head(200).to_dict(orient='records')
        return jsonify({'rows': rows})
    except Exception as e:
        return jsonify({'error': f'获取详情失败: {str(e)}'}, 500)



# 临时文件访问（预览） & 下载 & 删除
@app.route('/tmp_data/<path:filename>/<site>')
def serve_tmp_data(filename, site):
    site_path = os.path.join(TMP_DIR, site)
    file_path = os.path.join(site_path, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    # 目录与文件名分开传
    base_dir = os.path.dirname(file_path)
    fname = os.path.basename(file_path)
    return send_from_directory(base_dir, fname)


@app.route('/delete_dataset/<path:filename>/<site>', methods=['DELETE'])
def delete_dataset(filename, site):
    filename = unquote(filename)
    site_dir = os.path.join(TMP_DIR, site)
    file_path = os.path.join(site_dir, filename)

    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": f"{filename} 不存在"})

    try:
        os.remove(file_path)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/tmp_data_preview/<path:filename>/<site>')
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
        return jsonify({'error': f'获取详情失败: {str(e)}'}, 500)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
