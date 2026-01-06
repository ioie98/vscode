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
import pymysql
from decimal import Decimal
from flask import abort
from tos import TosClientV2



app = Flask(__name__)
CORS(app)

# 数据目录
TMP_DIR = "tmp_data"
# 全局进度字典
progress_dict = {}
os.makedirs(TMP_DIR, exist_ok=True)


# ClickHouse 配置
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
DEFAULT_SOURCE_PRIORITY = ['Device', 'cros', 'ec', 'era5']

# MySQL 配置
MYSQL_CONFIG = {
    'host': '115.190.81.184',
    'port': 30730,
    'user': 'gnss',
    'password': 'klv!dopY$uN8I',
    'database': 'gnss',
    'charset': 'utf8mb4'
}

# 获取站点选项
@app.route('/get_station_options', methods=['GET'])
def get_station_options():
    try:
        with open('static/stations.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        print("读取 stations.json 失败:", e)
        return jsonify([]), 500


# 查询站点名称
def get_site_name(site_id):
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor() as cursor:
            sql = "SELECT NAME FROM sb_jbxx WHERE ID=%s"
            cursor.execute(sql, (site_id,))
            res = cursor.fetchone()
        conn.close()
        if res:
            return res[0]
        return site_id
    except Exception as e:
        print(f"获取站点名称失败: {e}")
        return site_id


# 根据项目 XMID 获取站点（站名 + 站号）
@app.route('/get_sites_by_project', methods=['GET'])
def get_sites_by_project():
    xmid = request.args.get("xmid")

    if not xmid:
        return jsonify([])

    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor() as cursor:

            sql = """
                SELECT 
                    sb.NAME AS site_name,   -- 中文站名
                    sb.ID AS site_id        -- 站号，如 b177
                FROM sggl_zd zd
                JOIN sb_jbxx sb 
                    ON zd.ID = sb.STATION_ID
                WHERE zd.XMID = %s
            """

            cursor.execute(sql, (xmid,))
            rows = cursor.fetchall()
        conn.close()

        sites = [{"MC": r[0], "ID": r[1]} for r in rows]

        return jsonify(sites)

    except Exception as e:
        print("读取站点失败:", e)
        return jsonify([]), 500





# 获取项目列表（项目ID + 项目名称）
@app.route('/get_projects', methods=['GET'])
def get_projects():
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor() as cursor:
            sql = "SELECT ID, MC FROM sggl_xm"
            cursor.execute(sql)
            rows = cursor.fetchall()
        conn.close()

        # XMID = 项目ID（前端用 XMID 字段）
        projects = [{"XMID": r[0], "MC": r[1]} for r in rows]

        return jsonify(projects)

    except Exception as e:
        print("读取项目列表失败:", e)
        return jsonify([]), 500




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
        dtype = request.form.get('type')  # rain / pwv / weather
        device = request.form.get('device') or request.form.get('station_id')

        if not dtype or not device:
            return jsonify({'error': '缺少类型或设备参数'}), 400
        if dtype not in TABLE_CONFIG:
            return jsonify({'error': f'未知类型: {dtype}'}), 400

        cfg = TABLE_CONFIG[dtype]
        table = cfg['table']
        fields = [f.lower() for f in cfg['fields']]

        # 读取 CSV 并统一列名小写
        df = pd.read_csv(file, encoding='utf-8-sig')
        df.columns = [c.strip().lower() for c in df.columns]

        # 找到时间列
        time_col = next((c for c in df.columns if 'data_time' in c or '时间' in c), None)
        if not time_col:
            return jsonify({'status': 'success', 'inserted_count': 0, 'error': '无时间列'})

        # 转换函数
        def to_float(x):
            try:
                if x is None or str(x).strip() == '':
                    return None
                return float(str(x).strip())
            except:
                return None

        def to_int16(x):
            try:
                if x is None or str(x).strip() == '':
                    return None
                return int(float(str(x).strip()))
            except:
                return None

        def to_int8(x):
            try:
                if x is None or str(x).strip() == '':
                    return None
                return int(float(str(x).strip()))
            except:
                return None

        # 多列匹配
        def get_column_value(row, possible_cols):
            for col in possible_cols:
                if col in row:
                    return row[col]
            return None

        buffer_list = []
        for _, row in df.iterrows():
            dt_str = str(row.get(time_col))
            dt = pd.to_datetime(dt_str, errors='coerce')
            if pd.isna(dt):
                continue
            dt_utc = dt - pd.Timedelta(hours=8)

            item = None
            if dtype == 'pwv':
                item = {
                    'data_time': dt_utc,
                    'device': str(row.get('device', device)),
                    'lon': to_float(get_column_value(row, ['lon'])),
                    'lau': to_float(get_column_value(row, ['lau'])),
                    'pwv': to_float(get_column_value(row, ['pwv'])),
                    'data_type': row.get('data_type', 'uploaded')
                }
                # 跳过 lon/lau/pwv 都为空
                if item['lon'] is None and item['lau'] is None and item['pwv'] is None:
                    continue

            elif dtype == 'weather':
                item = {
                    'data_time': dt_utc,
                    'device': str(row.get('device', device)),
                    'ta': to_float(row.get('ta')),
                    'pa': to_float(row.get('pa')),
                    'ua': to_float(row.get('ua')),
                    'data_type': row.get('data_type', 'uploaded')
                }
            elif dtype == 'rain':
                item = {
                    'data_time': dt_utc,
                    'device': str(row.get('device', device)),
                    'rainfall': to_float(row.get('rainfall')),
                    'data_type': row.get('data_type', 'uploaded'),
                    'rain_time': to_int16(row.get('rain_time')),
                    'reset': to_int8(row.get('reset'))
                }

            if item:
                buffer_list.append(item)

        if not buffer_list:
            return jsonify({'status': 'success', 'inserted_count': 0, 'error': '无有效数据'})

        # 去重
        min_t = min(r['data_time'] for r in buffer_list)
        max_t = max(r['data_time'] for r in buffer_list)
        existing_keys = set()
        try:
            q = f"""
                SELECT data_time, data_type FROM {table}
                WHERE device = '{device}'
                AND data_time >= toDateTime('{min_t:%Y-%m-%d %H:%M:%S}', 'UTC')
                AND data_time <= toDateTime('{max_t:%Y-%m-%d %H:%M:%S}', 'UTC')
                AND data_type = '{dtype}'
            """
            res = client.query(q)
            for r in res.result_rows:
                existing_keys.add(r[0].strftime("%Y-%m-%d %H:%M:%S"))
        except:
            existing_keys = set()

        buffer_list = [
            r for r in buffer_list
            if r['data_time'].strftime("%Y-%m-%d %H:%M:%S") not in existing_keys
        ]

        # 插入 ClickHouse
        records = [[r.get(f, None) for f in fields] for r in buffer_list]
        inserted_count = 0
        if records:
            try:
                client.insert(table, records, column_names=fields)
                inserted_count = len(records)
            except Exception as e:
                print("ClickHouse 插入失败:", e)
                traceback.print_exc()

        return jsonify({
            'status': 'success',
            'inserted_count': inserted_count,
            'start_time': min_t.strftime("%Y/%m/%d %H:%M:%S"),
            'end_time': max_t.strftime("%Y/%m/%d %H:%M:%S")
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

    # 保存到 mode/site 目录
    site_dir = os.path.join(TMP_DIR, data.get('mode') or 'train', device)
    os.makedirs(site_dir, exist_ok=True)
    start_str = start_dt.strftime("%Y-%m-%d_%H-%M-%S")
    end_str = end_dt.strftime("%Y-%m-%d_%H-%M-%S")

    tmp_file_name = f"{data_type}_{start_str}_{end_str}.csv"
    tmp_file = os.path.join(site_dir, tmp_file_name)
    pd.DataFrame(data_list).to_csv(tmp_file, index=False, encoding='utf-8-sig')

    # 返回相对路径（mode/site/filename）
    rel_path = os.path.join(data.get('mode') or 'train', device, tmp_file_name)

    return jsonify({
        'count': len(data_list),
        'data': data_list[:1000],
        'tmp_file': rel_path
    })


# 单站点单类型下载
def _download_single_type_for_device(device, data_type, start_time, end_time, priority_list, mode='train'):
    config = TABLE_CONFIG.get(data_type)
    if not config:
        return {'type': data_type, 'count': -1, 'error': '未知数据类型'}

    table = config['table']
    fields = config['fields']

    try:
        # 北京时间 → UTC
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

    # 保存到 mode/site 子目录
    site_dir = os.path.join(TMP_DIR, mode, device)
    os.makedirs(site_dir, exist_ok=True)

    start_str = start_local.strftime("%Y-%m-%d_%H-%M-%S")
    end_str = end_local.strftime("%Y-%m-%d_%H-%M-%S")
    tmp_file_name = f"{data_type}_{start_str}_{end_str}.csv"
    tmp_file = os.path.join(site_dir, tmp_file_name)

    try:
        pd.DataFrame(data_list).to_csv(tmp_file, index=False, encoding='utf-8-sig')
    except Exception as e:
        return {'type': data_type, 'count': -1, 'error': f'保存失败: {str(e)}'}

    rel_path = os.path.join(mode, device, tmp_file_name)
    return {'type': data_type, 'count': len(data_list), 'tmp_file': rel_path}


# 批量下载接口（自动整合）
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
        mode = (payload.get('mode') or 'train').lower()

        if not devices and single_device:
            devices = [single_device]

        if not all([types, start_time, end_time, devices]):
            return jsonify({'error': '参数缺失(types/start_time/end_time/devices)'}), 400

        priority_list = [str(p).lower() for p in priority if p]
        overall_results = []
 
        for device in devices:
            device_result = {'device': device, 'results': []}
            try:
                for data_type in types:
                    res = _download_single_type_for_device(device, data_type, start_time, end_time, priority_list, mode=mode)
                    device_result['results'].append(res)
                overall_results.append(device_result)
            except Exception as e:
                device_result['results'].append({'type': 'internal', 'count': -1, 'error': f'内部异常: {str(e)}'})
                overall_results.append(device_result)

        # 下载完成后自动合并到对应 mode 目录
        try:
            merged = merge_datasets_inner(devices, mode)

            if isinstance(merged, list):
                for m in merged:
                    site_id = m.get('site_id') or m.get('device') or ''
                    m['site_name'] = get_site_name(site_id)
            elif isinstance(merged, dict) and 'results' in merged:
                for m in merged['results']:
                    site_id = m.get('site_id') or m.get('device') or ''
                    m['site_name'] = get_site_name(site_id)

        except Exception as e:
            merged = {'status': 'error', 'message': f'合并异常: {str(e)}', 'trace': traceback.format_exc()}

        return jsonify({'status': 'success', 'details': overall_results, 'merged': merged})
    except Exception as e:
        traceback_str = traceback.format_exc()
        return jsonify({'error': f'批量下载失败: {str(e)}', 'trace': traceback_str}), 500


# 接收站点列表并合并（只合并本次下载的文件）
def merge_datasets_inner(sites, mode='train'):
    """
    合并 TMP_DIR/{mode}/{site}/ 下本次下载的 pwv/weather/rain CSV
    并输出一个最终的合并文件：
        {site}_{YYMMDD_start}_{YYMMDD_end}_{Device|Mix}.csv
    """
    results = []

    # 从 request 中取出优先级（如果存在）
    try:
        from flask import request
        payload = request.get_json(silent=True) or {}
        priority_list = [str(p).lower() for p in payload.get("priority", []) if p]
        if not priority_list:
            priority_list = [str(p).lower() for p in DEFAULT_SOURCE_PRIORITY]
    except:
        priority_list = [str(p).lower() for p in DEFAULT_SOURCE_PRIORITY]

    # 判断后缀（Device / Mix）
    top_source = priority_list[0] if priority_list else "mix"
    suffix = "Device" if top_source == "device" else "Mix"

    for site in sites:
        site = str(site)
        mode_dir = os.path.join(TMP_DIR, mode, site)

        if not os.path.exists(mode_dir):
            results.append({'site_id': site, 'error': f'{mode} 目录不存在'})
            continue

        # 本次下载生成的文件（排除已经合并过的）
        csv_files = []
        for f in os.listdir(mode_dir):
            full = os.path.join(mode_dir, f)
            if not (os.path.isfile(full) and f.lower().endswith('.csv')):
                continue

            # 已合并文件：站点 + _XXXXXX_XXXXXX_*.csv
            # 例如：b100_250502_250717_Device.csv
            if re.match(rf'^{re.escape(site)}_\d{{6}}_\d{{6}}_', f, re.I):
                continue

            csv_files.append(full)

        if not csv_files:
            results.append({'site_id': site, 'error': f'{mode} 目录下无可合并 CSV'})
            continue

        # 读取并标准化
        standardized_dfs = []

        for fpath in csv_files:
            try:
                df = pd.read_csv(fpath, encoding='utf-8-sig')
            except:
                try:
                    df = pd.read_csv(fpath)
                except:
                    continue

            # 找时间列
            time_col_candidates = ['data_time', 'date', 'time']
            time_col = next((c for c in df.columns if c.lower() in time_col_candidates or '时间' in c), None)
            if not time_col:
                continue

            df = df.rename(columns={time_col: 'date'})
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date']).set_index('date')

            # 列映射
            col_map = {
                'ta': 't2m', 't2m': 't2m',
                'pa': 'sp',  'sp':  'sp',
                'ua': 'rh',  'rh':  'rh',
                'pwv': 'pwv',
                'rainfall': 'tp',
                'tp': 'tp'
            }

            std_df = pd.DataFrame(index=df.index)
            for c in df.columns:
                ck = c.strip().lower()
                if ck in col_map:
                    try:
                        std_df[col_map[ck]] = pd.to_numeric(df[c], errors='coerce').round(3)
                    except:
                        std_df[col_map[ck]] = np.nan

            # 缺少的列补齐
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

        merged = merged.sort_index().reset_index().rename(columns={'index': 'date'})
        merged['date'] = merged['date'].dt.strftime('%Y/%m/%d %H:%M:%S')

        # 生成文件名
        first_date = pd.to_datetime(merged['date'], errors='coerce').min()
        last_date = pd.to_datetime(merged['date'], errors='coerce').max()

        start_name = first_date.strftime('%Y%m%d') if pd.notna(first_date) else datetime.now().strftime('%Y%m%d')
        end_name   = last_date.strftime('%Y%m%d') if pd.notna(last_date) else datetime.now().strftime('%Y%m%d')

        start_short = start_name[2:]  # YYMMDD
        end_short   = end_name[2:]    # YYMMDD

        dataset_name = f"{site}_{start_short}_{end_short}_{suffix}.csv"

        # 保存合并文件
        merged_path = os.path.join(mode_dir, dataset_name)
        try:
            merged.to_csv(merged_path, index=False, encoding='utf-8-sig')
        except Exception as e:
            results.append({'site_id': site, 'error': f'保存合并文件失败: {str(e)}'})
            continue

        #删除本次下载的原始 CSV 文件
        for fpath in csv_files:
            try:
                os.remove(fpath)
            except:
                pass

        # 返回结果
        results.append({
            'site_id': site,
            'sub_dir': mode,
            'dataset': dataset_name,
            'suffix': suffix,
            'time_range': f"{first_date.strftime('%Y/%m/%d %H:%M:%S')} ~ {last_date.strftime('%Y/%m/%d %H:%M:%S')}"
        })

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




# 获取站点数据
@app.route('/get_datasets')
def get_datasets_route():
    site = request.args.get('site')

    if not site:
        # 返回站点列表（扫描 train/ 和 pred/ 下的子目录）
        sites = set()
        for mode in ['train', 'pred']:
            mode_dir = os.path.join(TMP_DIR, mode)
            if os.path.exists(mode_dir):
                for d in os.listdir(mode_dir):
                    p = os.path.join(mode_dir, d)
                    if os.path.isdir(p):
                        sites.add(d)
        site_list = []
        for s in sorted(sites):
            site_name = get_site_name(s)
            site_list.append({'site_id': s, 'site_name': site_name})
        return jsonify(site_list)

    site = site.strip()

    train_dir = os.path.join(TMP_DIR, "train", site)
    pred_dir = os.path.join(TMP_DIR, "pred", site)

    def list_mode_files(mode_dir, mode):
        out = []
        if os.path.exists(mode_dir):
            for file in os.listdir(mode_dir):
                # 只处理 csv
                if file.endswith('.csv'):
                    path = os.path.join(mode, site, file)
                    # 读取 CSV 获取时间范围
                    try:
                        df = pd.read_csv(os.path.join(mode_dir, file))
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
                        "site_name": get_site_name(site),
                        "start_time": start_time,
                        "end_time": end_time,
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(os.path.join(mode_dir, file)))),
                        "path": os.path.join(mode, site, file)
                    })
        return out

    train_files = list_mode_files(train_dir, "train")
    pred_files = list_mode_files(pred_dir, "pred")

    # 按文件创建时间倒序
    train_files.sort(key=lambda x: os.path.getctime(os.path.join(TMP_DIR, x['path'])), reverse=True) if train_files else None
    pred_files.sort(key=lambda x: os.path.getctime(os.path.join(TMP_DIR, x['path'])), reverse=True) if pred_files else None

    return jsonify({"train": train_files, "pred": pred_files})



# 获取文件行
@app.route('/get_file_rows')
def get_file_rows():
    site = request.args.get('site')
    mode = request.args.get('mode')
    file = request.args.get('file')

    if not all([site, mode, file]):
        return jsonify({'error': '参数缺失(site/mode/file)'}), 400

    # 防止路径注入
    if '/' in file or '\\' in file:
        file = os.path.basename(file)

    file_path = os.path.join(TMP_DIR, mode, site, file)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    try:
        df = pd.read_csv(file_path)
        # 清理列并输出前 200 行
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
    try:
        filename = unquote(filename)
        parts = filename.split('/', 1)
        if len(parts) == 2:
            mode, fname = parts
            file_path = os.path.join(TMP_DIR, mode, site, fname)
        else:
            fname = parts[0]
            possible = None
            for m in ['train', 'pred']:
                p = os.path.join(TMP_DIR, m, site, fname)
                if os.path.exists(p):
                    possible = p
                    break
            if possible:
                file_path = possible
            else:
                file_path = os.path.join(TMP_DIR, filename)

        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404

        base_dir = os.path.dirname(file_path)
        fname = os.path.basename(file_path)
        return send_from_directory(base_dir, fname)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#删除数据集
@app.route('/delete_dataset/<path:filename>/<site>', methods=['DELETE'])
def delete_dataset(filename, site):
    from urllib.parse import unquote
    filename = unquote(filename)
    site = site or ''

    # 直接在 TMP_DIR 下按完整路径查找
    file_path = os.path.join(TMP_DIR, filename)

    # 尝试在 train/pred 下查找（兼容旧路径）
    found = os.path.exists(file_path)
    if not found:
        for m in ['train', 'pred']:
            p = os.path.join(TMP_DIR, m, site, os.path.basename(filename))
            if os.path.exists(p):
                file_path = p
                found = True
                break

    # 即使文件不存在，也返回 success，让前端移除表格
    if found:
        try:
            os.remove(file_path)
        except Exception as e:
            # 删除失败也返回 success，但带错误信息
            return jsonify({"status": "success", "message": f"删除失败: {str(e)}"})
    else:
        # 文件已不存在
        return jsonify({"status": "success", "message": "文件已不存在"})

    return jsonify({"status": "success"})




# # 临时文件预览数据接口
# @app.route('/tmp_data_preview/<path:filename>/<site>')
# def tmp_data_preview(filename, site):
#     filename = unquote(filename)
#     parts = filename.split('/', 1)
#     if len(parts) == 2:
#         mode, fname = parts
#         path = os.path.join(TMP_DIR, mode, site, fname)
#     else:
#         found = False
#         path = ''
#         for m in ['train', 'pred']:
#             p = os.path.join(TMP_DIR, m, site, filename)
#             if os.path.exists(p):
#                 path = p
#                 found = True
#                 break
#         if not found:
#             path = os.path.join(TMP_DIR, filename)

#     if not os.path.exists(path):
#         return jsonify({'error': '文件不存在'}), 404
#     try:
#         df = pd.read_csv(path)

#         def clean_columns(col_base):
#             for suffix in ['', '_x', '_y']:
#                 if col_base + suffix in df.columns:
#                     return df[col_base + suffix]

#             for c in df.columns:
#                 if c.lower() in [col_base, col_base.lower()]:
#                     return df[c]
#             return pd.Series([None]*len(df))

#         clean_df = pd.DataFrame({
#             'date': clean_columns('date') if 'date' in df.columns else clean_columns('data_time'),
#             't2m': clean_columns('t2m'),
#             'sp': clean_columns('sp'),
#             'rh': clean_columns('rh'),
#             'pwv': clean_columns('pwv'),
#             'tp': clean_columns('tp')
#         })

#         clean_df['date'] = pd.to_datetime(clean_df['date'], errors='coerce').dt.strftime('%Y/%m/%d %H:%M:%S')
#         clean_df = clean_df.where(pd.notnull(clean_df), None)
#         preview_rows = clean_df.head(100).to_dict(orient='records')
#         return jsonify({'rows': preview_rows})
#     except Exception as e:
#         return jsonify({'error': f'获取详情失败: {str(e)}'}, 500)

#数据集下载接口
@app.route("/download_dataset/<path:filepath>")
def download_dataset(filepath):
    """
    filepath 示例：train/b100/b100_250405_250417_Mix.csv
    """

    try:
        filepath = filepath.replace("\\", "/")
        full_path = os.path.join(TMP_DIR, filepath)
        # print("准备下载：", full_path)

        # 文件不存在则返回404
        if not os.path.exists(full_path):
            print("文件不存在：", full_path)
            return abort(404, "文件不存在")

        # 文件所在文件夹 & 文件名
        folder, filename = os.path.split(full_path)

        # 下载文件
        return send_from_directory(folder, filename, as_attachment=True)

    except Exception as e:
        print("下载异常:", e)
        return abort(500, "服务器下载异常")


# TOS 上传接口   
# 配置 TOS
endpoint = "tos-cn-beijing.volces.com"
region = "cn-beijing"
bucket_name = "model-file"
ak = os.getenv('TOS_ACCESS_KEY', '你的AK')
sk = os.getenv('TOS_SECRET_KEY', '你的SK')

# 初始化客户端
tos_client = TosClientV2(ak, sk, endpoint, region)

# 临时目录
TMP_DIR = "tmp_data"
os.makedirs(TMP_DIR, exist_ok=True)

@app.route('/upload_to_tos', methods=['POST'])
def upload_to_tos():
    try:
        req = request.get_json()
        site = req.get('site')       # 如 b72
        mode = req.get('mode')       # 如 train
        filename = req.get('filename')

        if not site or not mode or not filename:
            return jsonify({'status':'error', 'error':'缺少参数'}), 400

        # 本地文件路径
        file_path = os.path.join(TMP_DIR, mode, site, filename)

        if not os.path.isfile(file_path):
            return jsonify({'status':'error', 'error':'文件不存在'}), 400

        # 上传到 TOS 的 key
        key = f"{mode}/{site}/quantitative/{filename}"

        #上传文件到 TOS
        with open(file_path, 'rb') as f:
            tos_client.put_object(
                bucket=bucket_name,
                key=key,
                content=f.read()
            )

        # 调用外部 API /api/datasets/upload
        #    file_abs_path 格式要求：tos://bucket/mode/site/quantitative
        file_abs_path = f"tos://{bucket_name}/{mode}/{site}/quantitative"

        payload = {
            "file_abs_path": file_abs_path,
            "file_name": filename
        }

        try:
            resp = requests.post(
                "http://120.46.164.250:5000/api/datasets/upload",
                json=payload,
                timeout=30
            )
            upload_api_result = resp.json()
        except Exception as e:
            upload_api_result = {"error": f"调用远程接口失败: {str(e)}"}

        return jsonify({
            'status': 'success',
            'tos_key': key,
            'dataset_upload_response': upload_api_result
        })

    except Exception as e:
        return jsonify({'status':'error', 'error': str(e)}), 500





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
