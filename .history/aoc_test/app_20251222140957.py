from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from flask_cors import CORS
import clickhouse_connect
from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np
import time
import traceback
import re
from urllib.parse import unquote
import json
import pymysql
import requests
from tos import TosClientV2

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# ---------------- 配置常量 ----------------

TMP_DIR = "tmp_data"
os.makedirs(TMP_DIR, exist_ok=True)  # 确保临时数据目录存在

# ClickHouse 数据库配置
CLICKHOUSE_CONFIG = {
    'host': 'bytehouse.huoshan.accurain.cn',
    'port': 80,
    'username': 'accuraindev',
    'password': '2P%#9N8qVSb@sQ',
    'database': 'dev',
    'compression': 'gzip'
}

# MySQL 数据库配置
MYSQL_CONFIG = {
    'host': '115.190.81.184',
    'port': 30730,
    'user': 'gnss',
    'password': 'klv!dopY$uN8I',
    'database': 'gnss',
    'charset': 'utf8mb4'
}

# TOS (对象存储) 配置
TOS_CFG = {
    'endpoint': "tos-cn-beijing.volces.com",
    'region': "cn-beijing",
    'bucket': "model-file",
    'ak': os.getenv('TOS_ACCESS_KEY', '你的AK'),
    'sk': os.getenv('TOS_SECRET_KEY', '你的SK')
}

# 数据表字段映射配置
TABLE_CONFIG = {
    'pwv': {'table': 'ods_pwv_external', 'fields': ['data_time', 'device', 'pwv', 'data_type']},
    'weather': {'table': 'ods_hws_external', 'fields': ['data_time', 'device', 'ta', 'pa', 'ua', 'data_type']},
    'rain': {'table': 'ods_raingauge_external', 'fields': ['data_time', 'device', 'rainfall', 'data_type']}
}

# CSV 列名标准化映射
COL_MAP = {
    'ta': 't2m', 't2m': 't2m', # 温度
    'pa': 'sp',  'sp':  'sp',  # 气压
    'ua': 'rh',  'rh':  'rh',  # 湿度
    'pwv': 'pwv',              # PWV
    'rainfall': 'tp', 'tp': 'tp' # 降雨量
}

# 默认的数据源优先级
DEFAULT_SOURCE_PRIORITY = ['Device', 'cros', 'ec', 'era5']

# 初始化客户端
client = clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)
tos_client = TosClientV2(TOS_CFG['ak'], TOS_CFG['sk'], TOS_CFG['endpoint'], TOS_CFG['region'])

# ---------------- 辅助函数 ----------------

def get_db_connection():
    """获取 MySQL 连接"""
    return pymysql.connect(**MYSQL_CONFIG)

def get_site_name(site_id):
    """根据站点ID查询站点中文名称 (查MySQL)"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT NAME FROM sb_jbxx WHERE ID=%s", (site_id,))
            res = cursor.fetchone()
        conn.close()
        return res[0] if res else site_id
    except Exception as e:
        print(f"获取站点名称失败: {e}")
        return site_id

def to_float(x):
    """安全转换为浮点数"""
    try:
        return float(str(x).strip()) if x is not None and str(x).strip() != '' else None
    except: return None

def get_file_absolute_path(filename, site='', mode=''):
    """统一解析文件路径"""
    filename = unquote(filename)
    
    # 拼接完整路径
    if mode and site:
        direct_path = os.path.join(TMP_DIR, mode, site, filename)
        if os.path.exists(direct_path): return direct_path

    # 2. 尝试作为根目录下的相对路径
    rel_path = os.path.join(TMP_DIR, filename)
    if os.path.exists(rel_path): return rel_path

    # 3. 遍历 train/pred 目录搜索文件
    for m in ['train', 'pred']:
        p = os.path.join(TMP_DIR, m, site or '', os.path.basename(filename))
        if os.path.exists(p): return p

    return None

# ---------------- 路由接口 ----------------

@app.route('/')
def index():
    return render_template('index.html')

## 站点列表
@app.route('/get_station_options', methods=['GET'])
def get_station_options():
    try:
        with open('static/stations.json', 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except: return jsonify([])

## 站点数据
@app.route('/get_projects', methods=['GET'])
def get_projects():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT ID, MC FROM sggl_xm")
            rows = [{"XMID": r[0], "MC": r[1]} for r in cursor.fetchall()]
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify([]), 500

@app.route('/get_sites_by_project', methods=['GET'])
def get_sites_by_project():
    xmid = request.args.get("xmid")
    if not xmid: return jsonify([])
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT sb.NAME, sb.ID FROM sggl_zd zd JOIN sb_jbxx sb ON zd.ID = sb.STATION_ID WHERE zd.XMID = %s"
            cursor.execute(sql, (xmid,))
            rows = [{"MC": r[0], "ID": r[1]} for r in cursor.fetchall()]
        conn.close()
        return jsonify(rows)
    except: return jsonify([]), 500

# 上传数据
@app.route('/upload_data', methods=['POST'])
def upload_data():
    try:
        if 'file' not in request.files: return jsonify({'error': '未检测到文件'}), 400
        file = request.files['file']
        dtype = request.form.get('type')
        device = request.form.get('device') or request.form.get('station_id')
        
        if not dtype or not device or dtype not in TABLE_CONFIG:
            return jsonify({'error': '参数错误或未知类型'}), 400

        cfg = TABLE_CONFIG[dtype]
        df = pd.read_csv(file, encoding='utf-8-sig')
        df.columns = [c.strip().lower() for c in df.columns]

        time_col = next((c for c in df.columns if 'data_time' in c or '时间' in c), None)
        if not time_col: return jsonify({'status': 'success', 'inserted_count': 0, 'error': '无时间列'})

        buffer = []
        for _, row in df.iterrows():
            dt = pd.to_datetime(row.get(time_col), errors='coerce')
            if pd.isna(dt): continue
            dt_utc = dt - pd.Timedelta(hours=8)
            
            item = {
                'data_time': dt_utc,
                'device': str(row.get('device', device)),
                'data_type': row.get('data_type', 'uploaded')
            }

            if dtype == 'pwv':
                item.update({'pwv': to_float(row.get('pwv'))})
                if item['pwv'] is None and to_float(row.get('lon')) is None: continue 
            elif dtype == 'weather':
                item.update({
                    'ta': to_float(row.get('ta')), 
                    'pa': to_float(row.get('pa')), 
                    'ua': to_float(row.get('ua'))
                })
            elif dtype == 'rain':
                item['rainfall'] = to_float(row.get('rainfall'))

            buffer.append(item)

        if not buffer: return jsonify({'status': 'success', 'inserted_count': 0})

        min_t, max_t = min(x['data_time'] for x in buffer), max(x['data_time'] for x in buffer)
        
        fields = cfg['fields']
        data_to_insert = [[r.get(f) for f in fields] for r in buffer]
        client.insert(cfg['table'], data_to_insert, column_names=fields)

        return jsonify({
            'status': 'success',
            'inserted_count': len(data_to_insert),
            'start_time': min_t.strftime("%Y/%m/%d %H:%M:%S"),
            'end_time': max_t.strftime("%Y/%m/%d %H:%M:%S")
        })

    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

# 下载数据
def _download_single_type(device, data_type, start_utc, end_utc, priority, mode):
    cfg = TABLE_CONFIG.get(data_type)
    if not cfg: return {'type': data_type, 'count': -1, 'error': '未知类型'}

    merged_data = {}
    for source in priority:
        query = f"""
            SELECT {', '.join(cfg['fields'])} FROM {cfg['table']}
            WHERE device = '{device}' 
            AND data_time BETWEEN toDateTime('{start_utc}', 'UTC') AND toDateTime('{end_utc}', 'UTC')
            AND LOWER(data_type) = '{source}'
            ORDER BY data_time ASC LIMIT 100000
        """
        try:
            res = client.query(query)
            for row in [dict(zip(res.column_names, r)) for r in res.result_rows]:
                t_str = (row['data_time'] + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                if t_str not in merged_data:
                    row['data_time'] = t_str
                    merged_data[t_str] = row
        except Exception as e:
            return {'type': data_type, 'count': -1, 'error': str(e)}

    if not merged_data: return {'type': data_type, 'count': 0}

    site_dir = os.path.join(TMP_DIR, mode, device)
    os.makedirs(site_dir, exist_ok=True)
    
    fname = f"{data_type}_{start_utc.replace(':','-')}_{end_utc.replace(':','-')}.csv"
    fpath = os.path.join(site_dir, fname)
    pd.DataFrame(merged_data.values()).to_csv(fpath, index=False, encoding='utf-8-sig')
    
    return {'type': data_type, 'count': len(merged_data), 'tmp_file': os.path.join(mode, device, fname)}

# 批量下载接口
@app.route('/batch_download', methods=['POST'])
def batch_download():
    data = request.json or {}
    types = data.get('types', [])
    devices = data.get('devices') or ([data.get('device')] if data.get('device') else [])
    priority = [p.lower() for p in (data.get('priority') or DEFAULT_SOURCE_PRIORITY)]
    mode = data.get('mode', 'train').lower()

    if not all([types, data.get('start_time'), data.get('end_time'), devices]):
        return jsonify({'error': '参数缺失'}), 400

    try:
        s_dt = datetime.fromisoformat(data['start_time']) - timedelta(hours=8)
        e_dt = datetime.fromisoformat(data['end_time']) - timedelta(hours=8)
        s_str, e_str = s_dt.strftime("%Y-%m-%d %H:%M:%S"), e_dt.strftime("%Y-%m-%d %H:%M:%S")

        details = []
        for dev in devices:
            dev_res = {'device': dev, 'results': []}
            for t in types:
                dev_res['results'].append(_download_single_type(dev, t, s_str, e_str, priority, mode))
            details.append(dev_res)

        merged_res = merge_datasets_inner(devices, mode, priority)
        
        if 'results' in merged_res:
            for m in merged_res['results']:
                m['site_name'] = get_site_name(m['site_id'])

        return jsonify({'status': 'success', 'details': details, 'merged': merged_res})
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

# 数据合并
def merge_datasets_inner(sites, mode, priority=None):
    results = []
    suffix = "Device" if (priority and priority[0] == 'device') else "Mix"

    for site in sites:
        mode_dir = os.path.join(TMP_DIR, mode, site)
        if not os.path.exists(mode_dir): continue

        csv_files = [
            os.path.join(mode_dir, f) for f in os.listdir(mode_dir)
            if f.endswith('.csv') and not re.match(rf'^{re.escape(site)}_\d{{6}}_\d{{6}}_', f, re.I)
        ]
        
        if not csv_files: continue

        dfs = []
        for f in csv_files:
            try:
                df = pd.read_csv(f)
                time_col = next((c for c in df.columns if c.lower() in ['data_time', 'date', 'time']), None)
                if not time_col: continue
                
                df = df.rename(columns={time_col: 'date'})
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna(subset=['date']).set_index('date')
                
                std_df = pd.DataFrame(index=df.index)
                for c in df.columns:
                    target = COL_MAP.get(c.strip().lower())
                    if target: std_df[target] = pd.to_numeric(df[c], errors='coerce')
                
                dfs.append(std_df)
            except: continue

        if not dfs: continue
        
        final_df = dfs[0]
        for d in dfs[1:]: final_df = final_df.combine_first(d)
        
        for col in ['t2m', 'sp', 'rh', 'pwv', 'tp']:
            if col not in final_df.columns: final_df[col] = np.nan

        final_df = final_df.sort_index().reset_index()
        final_df['date'] = final_df['date'].dt.strftime('%Y/%m/%d %H:%M:%S')

        dates = pd.to_datetime(final_df['date'])
        start_fmt = dates.min().strftime('%y%m%d')
        end_fmt = dates.max().strftime('%y%m%d')
        fname = f"{site}_{start_fmt}_{end_fmt}_{suffix}.csv"
        
        final_df.to_csv(os.path.join(mode_dir, fname), index=False, encoding='utf-8-sig')

        for f in csv_files: os.remove(f)

        # 计算行数并返回 count
        results.append({
            'site_id': site, 'sub_dir': mode, 'dataset': fname,
            'count': len(final_df), 
            'time_range': f"{final_df['date'].iloc[0]} ~ {final_df['date'].iloc[-1]}"
        })

    return {'status': 'success', 'results': results}

# 获取数据集列表
@app.route('/get_datasets')
def get_datasets_route():
    target_site = request.args.get('site')
    
    if not target_site:
        sites = set()
        for m in ['train', 'pred']:
            p = os.path.join(TMP_DIR, m)
            if os.path.exists(p):
                sites.update([d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d))])
        return jsonify([{'site_id': s, 'site_name': get_site_name(s)} for s in sorted(sites)])

    resp = {}
    for mode in ['train', 'pred']:
        resp[mode] = []
        path = os.path.join(TMP_DIR, mode, target_site)
        if os.path.exists(path):
            for f in os.listdir(path):
                if not f.endswith('.csv'): continue
                full_p = os.path.join(path, f)
                
                #计算样本数量
                count = 0
                try:
                    df = pd.read_csv(full_p, usecols=[0]) 
                    count = len(df)
                except: 
                    count = 0
                
                resp[mode].append({
                    "name": f, "site": target_site, "site_name": get_site_name(target_site),
                    "count": count,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(full_p))),
                    "path": f
                })
    return jsonify(resp)

# 删除数据集
@app.route('/delete_dataset/<path:filename>/<site>', methods=['DELETE'])
def delete_dataset(filename, site):
    path = get_file_absolute_path(filename, site)
    if path:
        try:
            os.remove(path)
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "success", "message": "文件已不存在"})

# 下载数据集
@app.route("/download_dataset/<path:filepath>")
@app.route("/download_dataset/<mode>/<site>/<filename>")
def download_file_route(filepath=None, mode=None, site=None, filename=None):
    if not filepath: filepath = f"{mode}/{site}/{filename}"
    full_path = get_file_absolute_path(filepath, site)
    if full_path:
        return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path), as_attachment=True)
    return abort(404)

# 上传到 TOS 
@app.route('/upload_to_tos', methods=['POST'])
def upload_to_tos_route():
    """将生成的 CSV 文件上传到 TOS 对象存储"""
    try:
        data = request.json
        site, mode, fname = data.get('site'), data.get('mode'), data.get('filename')
        
        fpath = os.path.join(TMP_DIR, mode, site, fname)
        if not os.path.exists(fpath): 
            return jsonify({'status':'error', 'error':'文件不存在'}), 400

        # TOS 上传 Key
        key = f"{mode}/{site}/quantitative/{fname}"
        
        with open(fpath, 'rb') as f:
            tos_client.put_object(bucket=TOS_CFG['bucket'], key=key, content=f.read())
        
        print(f"TOS 上传成功: {key}")
        # 调用外部接口通知上传完成
        file_abs_path = f"tos://{TOS_CFG['bucket']}/{mode}/{site}/quantitative"
        
        payload = {
            "file_abs_path": file_abs_path,
            "file_name": fname
        }
        
        upload_api_result = {}
        cb_url = "http://120.46.164.250:5000/api/datasets/upload"
        
        try:
            print("调用上传接口，参数：", payload)
            resp = requests.post(
                cb_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if resp.status_code == 200:
                print(f"外部接口上传成功: {resp.text}")
                try:
                    upload_api_result = resp.json()
                except:
                    upload_api_result = {"msg": "回调成功但返回非JSON", "raw": resp.text}
            else:
                print(f"外部接口上传失败: HTTP {resp.status_code}, 内容: {resp.text}")
                upload_api_result = {"error": resp.text, "status_code": resp.status_code}
                
        except Exception as e:
            print(f"外部接口调用异常: {str(e)}")
            upload_api_result = {"error": f"调用远程接口失败: {str(e)}"}

        return jsonify({
            'status': 'success',
            'key': key,
            'dataset_upload_response': upload_api_result
        })

    except Exception as e:
        print(f"内部异常: {str(e)}")
        return jsonify({'status':'error', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)