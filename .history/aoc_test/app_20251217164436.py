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

# 数据表字段映射配置 (不同数据类型对应不同的表和字段)
TABLE_CONFIG = {
    'pwv': {'table': 'ods_pwv_external', 'fields': ['data_time', 'device', 'pwv', 'data_type']},
    'weather': {'table': 'ods_hws_external', 'fields': ['data_time', 'device', 'ta', 'pa', 'ua', 'data_type']},
    'rain': {'table': 'ods_raingauge_external', 'fields': ['data_time', 'device', 'rainfall', 'data_type']}
}

# CSV 列名标准化映射 (将不同来源的列名统一为标准格式)
COL_MAP = {
    'ta': 't2m', 't2m': 't2m', # 温度
    'pa': 'sp',  'sp':  'sp',  # 气压
    'ua': 'rh',  'rh':  'rh',  # 湿度
    'pwv': 'pwv',              # 大气可降水量
    'rainfall': 'tp', 'tp': 'tp' # 降雨量
}

# 默认的数据源优先级 (当同一时间点有多个数据源时，按此顺序取值)
DEFAULT_SOURCE_PRIORITY = ['Device', 'cros', 'ec', 'era5']

# 初始化数据库客户端
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
    """安全转换为浮点数，处理空值和非法字符"""
    try:
        return float(str(x).strip()) if x is not None and str(x).strip() != '' else None
    except: return None

def get_file_absolute_path(filename, site='', mode=''):
    """
    统一解析文件路径
    功能：无论前端传的是完整路径还是只有文件名，都能找到本地真实路径
    """
    filename = unquote(filename)
    
    # 拼接完整路径 (如 tmp_data/train/b100/xxx.csv)
    if mode and site:
        direct_path = os.path.join(TMP_DIR, mode, site, filename)
        if os.path.exists(direct_path): return direct_path

    # 根目录下的相对路径
    rel_path = os.path.join(TMP_DIR, filename)
    if os.path.exists(rel_path): return rel_path

    # 遍历 train/pred 目录搜索文件
    for m in ['train', 'pred']:
        p = os.path.join(TMP_DIR, m, site or '', os.path.basename(filename))
        if os.path.exists(p): return p

    return None

# ---------------- 路由接口 ----------------

@app.route('/')
def index():
    """渲染首页 HTML"""
    return render_template('index.html')

@app.route('/get_station_options', methods=['GET'])
def get_station_options():
    """获取所有可用站点列表 (从静态 JSON 文件读取)"""
    try:
        with open('static/stations.json', 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except: return jsonify([])

@app.route('/get_projects', methods=['GET'])
def get_projects():
    """获取所有项目列表 (从 MySQL 查询)"""
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
    """根据项目ID获取该项目下的所有站点 (从 MySQL 查询)"""
    xmid = request.args.get("xmid")
    if not xmid: return jsonify([])
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 联表查询：sggl_zd(项目站点关系) JOIN sb_jbxx(设备基本信息)
            sql = "SELECT sb.NAME, sb.ID FROM sggl_zd zd JOIN sb_jbxx sb ON zd.ID = sb.STATION_ID WHERE zd.XMID = %s"
            cursor.execute(sql, (xmid,))
            rows = [{"MC": r[0], "ID": r[1]} for r in cursor.fetchall()]
        conn.close()
        return jsonify(rows)
    except: return jsonify([]), 500

@app.route('/upload_data', methods=['POST'])
def upload_data():
    """
    上传 CSV 数据文件并写入 ClickHouse
    支持类型: pwv, weather, rain
    """
    try:
        if 'file' not in request.files: return jsonify({'error': '未检测到文件'}), 400
        file = request.files['file']
        dtype = request.form.get('type')
        device = request.form.get('device') or request.form.get('station_id')
        
        if not dtype or not device or dtype not in TABLE_CONFIG:
            return jsonify({'error': '参数错误或未知类型'}), 400

        cfg = TABLE_CONFIG[dtype]
        df = pd.read_csv(file, encoding='utf-8-sig')
        df.columns = [c.strip().lower() for c in df.columns] # 统一列名小写

        # 查找时间列
        time_col = next((c for c in df.columns if 'data_time' in c or '时间' in c), None)
        if not time_col: return jsonify({'status': 'success', 'inserted_count': 0, 'error': '无时间列'})

        buffer = []
        # 遍历 CSV 行，插入数据
        for _, row in df.iterrows():
            dt = pd.to_datetime(row.get(time_col), errors='coerce')
            if pd.isna(dt): continue
            dt_utc = dt - pd.Timedelta(hours=8) # 转换为 UTC 时间入库
            
            # 通用字段
            item = {
                'data_time': dt_utc,
                'device': str(row.get('device', device)),
                'data_type': row.get('data_type', 'uploaded')
            }

            # 根据类型提取特定字段
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

        # 计算时间范围
        min_t, max_t = min(x['data_time'] for x in buffer), max(x['data_time'] for x in buffer)
        
        # 批量插入 ClickHouse
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

def _download_single_type(device, data_type, start_utc, end_utc, priority, mode):
    """
    内部函数：下载单个类型的数据 (PWV/Weather/Rain)
    功能：从 ClickHouse 按照优先级(Device > EC > ERA5等) 查询并合并数据
    """
    cfg = TABLE_CONFIG.get(data_type)
    if not cfg: return {'type': data_type, 'count': -1, 'error': '未知类型'}

    merged_data = {}
    # 按照优先级顺序查询，后查到的会覆盖前面的(如果这里逻辑是 merge，通常应该是高优先级的先查并保留，或者反过来)
    # *当前逻辑是：priority 列表循环，source 不同的数据被合并到 merged_data 字典中，Key 是时间*
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
                # UTC 转北京时间供展示和文件保存
                t_str = (row['data_time'] + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                # 如果该时间点还没数据，则填入
                # *修正理解*：如果 merged_data 中没有 key，则插入。高优先级的先占位。
                if t_str not in merged_data:
                    row['data_time'] = t_str
                    merged_data[t_str] = row
        except Exception as e:
            return {'type': data_type, 'count': -1, 'error': str(e)}

    if not merged_data: return {'type': data_type, 'count': 0}

    # 保存单个类型的临时 CSV
    site_dir = os.path.join(TMP_DIR, mode, device)
    os.makedirs(site_dir, exist_ok=True)
    
    # 文件名生成
    fname = f"{data_type}_{start_utc.replace(':','-')}_{end_utc.replace(':','-')}.csv"
    fpath = os.path.join(site_dir, fname)
    pd.DataFrame(merged_data.values()).to_csv(fpath, index=False, encoding='utf-8-sig')
    
    return {'type': data_type, 'count': len(merged_data), 'tmp_file': os.path.join(mode, device, fname)}

@app.route('/batch_download', methods=['POST'])
def batch_download():
    """
    批量下载并整合接口
    功能：
    1. 根据时间范围和站点，分别下载 PWV、气象、雨量数据。
    2. 将这三种数据在服务器端自动合并成一个宽表 CSV。
    3. 返回整合后的文件信息。
    """
    data = request.json or {}
    types = data.get('types', [])
    devices = data.get('devices') or ([data.get('device')] if data.get('device') else [])
    priority = [p.lower() for p in (data.get('priority') or DEFAULT_SOURCE_PRIORITY)]
    mode = data.get('mode', 'train').lower()

    if not all([types, data.get('start_time'), data.get('end_time'), devices]):
        return jsonify({'error': '参数缺失'}), 400

    try:
        # 统一转UTC字符串
        s_dt = datetime.fromisoformat(data['start_time']) - timedelta(hours=8)
        e_dt = datetime.fromisoformat(data['end_time']) - timedelta(hours=8)
        s_str, e_str = s_dt.strftime("%Y-%m-%d %H:%M:%S"), e_dt.strftime("%Y-%m-%d %H:%M:%S")

        details = []
        # 下载各类型数据
        for dev in devices:
            dev_res = {'device': dev, 'results': []}
            for t in types:
                dev_res['results'].append(_download_single_type(dev, t, s_str, e_str, priority, mode))
            details.append(dev_res)

        # 自动合并 (Merge)
        merged_res = merge_datasets_inner(devices, mode, priority)
        
        # 补充站点名称供前端显示
        if 'results' in merged_res:
            for m in merged_res['results']:
                m['site_name'] = get_site_name(m['site_id'])

        return jsonify({'status': 'success', 'details': details, 'merged': merged_res})
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

def merge_datasets_inner(sites, mode, priority=None):
    """
    内部合并逻辑
    将下载在临时目录的 pwv.csv, weather.csv, rain.csv 根据时间对齐合并为一个最终数据集
    """
    results = []
    suffix = "Device" if (priority and priority[0] == 'device') else "Mix"

    for site in sites:
        mode_dir = os.path.join(TMP_DIR, mode, site)
        if not os.path.exists(mode_dir): continue

        # 查找该目录下本次下载生成的 CSV (排除掉已经是合并结果的文件)
        csv_files = [
            os.path.join(mode_dir, f) for f in os.listdir(mode_dir)
            if f.endswith('.csv') and not re.match(rf'^{re.escape(site)}_\d{{6}}_\d{{6}}_', f, re.I)
        ]
        
        if not csv_files: continue

        dfs = []
        # 读取所有 CSV
        for f in csv_files:
            try:
                df = pd.read_csv(f)
                # 统一列名和时间索引
                time_col = next((c for c in df.columns if c.lower() in ['data_time', 'date', 'time']), None)
                if not time_col: continue
                
                df = df.rename(columns={time_col: 'date'})
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna(subset=['date']).set_index('date')
                
                # 标准化列名 (如 ta -> t2m)
                std_df = pd.DataFrame(index=df.index)
                for c in df.columns:
                    target = COL_MAP.get(c.strip().lower())
                    if target: std_df[target] = pd.to_numeric(df[c], errors='coerce')
                
                dfs.append(std_df)
            except: continue

        if not dfs: continue
        
        # 执行合并
        final_df = dfs[0]
        for d in dfs[1:]: final_df = final_df.combine_first(d)
        
        # 确保所有标准列都存在，不存在补 NaN
        for col in ['t2m', 'sp', 'rh', 'pwv', 'tp']:
            if col not in final_df.columns: final_df[col] = np.nan

        final_df = final_df.sort_index().reset_index()
        final_df['date'] = final_df['date'].dt.strftime('%Y/%m/%d %H:%M:%S')

        # 生成最终文件名 (站点_开始时间_结束时间_后缀.csv)
        dates = pd.to_datetime(final_df['date'])
        start_fmt = dates.min().strftime('%y%m%d')
        end_fmt = dates.max().strftime('%y%m%d')
        fname = f"{site}_{start_fmt}_{end_fmt}_{suffix}.csv"
        
        final_df.to_csv(os.path.join(mode_dir, fname), index=False, encoding='utf-8-sig')

        # 清理文件
        for f in csv_files: os.remove(f)

        results.append({
            'site_id': site, 'sub_dir': mode, 'dataset': fname,
            'time_range': f"{final_df['date'].iloc[0]} ~ {final_df['date'].iloc[-1]}"
        })

    return {'status': 'success', 'results': results}

@app.route('/get_datasets')
def get_datasets_route():
    """
    获取数据集列表
    """
    target_site = request.args.get('site')
    
    # 1. 获取站点列表 (保持不变)
    if not target_site:
        sites = set()
        for m in ['train', 'pred']:
            p = os.path.join(TMP_DIR, m)
            if os.path.exists(p):
                sites.update([d for d in os.listdir(p) if os.path.isdir(os.path.join(p, d))])
        return jsonify([{'site_id': s, 'site_name': get_site_name(s)} for s in sorted(sites)])

    # 获取特定站点文件列表
    resp = {}
    for mode in ['train', 'pred']:
        resp[mode] = []
        path = os.path.join(TMP_DIR, mode, target_site)
        if os.path.exists(path):
            for f in os.listdir(path):
                if not f.endswith('.csv'): continue
                full_p = os.path.join(path, f)
                
                # --- 【核心修改】计算行数 ---
                count = 0
                try:
                    # 仅读取第一列来计算行数，速度快
                    df = pd.read_csv(full_p, usecols=[0]) 
                    count = len(df)
                except: 
                    count = 0
                # -------------------------
                
                resp[mode].append({
                    "name": f, 
                    "site": target_site, 
                    "site_name": get_site_name(target_site),
                    "count": count,  # <--- 必须有这个字段
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(full_p))),
                    "path": f
                })
    return jsonify(resp)

@app.route('/delete_dataset/<path:filename>/<site>', methods=['DELETE'])
def delete_dataset(filename, site):
    """删除指定的数据集文件"""
    path = get_file_absolute_path(filename, site)
    if path:
        try:
            os.remove(path)
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "success", "message": "文件已不存在"})

@app.route("/download_dataset/<path:filepath>")
@app.route("/download_dataset/<mode>/<site>/<filename>")
def download_file_route(filepath=None, mode=None, site=None, filename=None):
    """
    下载文件接口
    支持两种 URL 格式:
    1. /download_dataset/train/b100/data.csv (通过 filepath 捕获)
    2. /download_dataset/train/b100/data.csv (通过 mode/site/filename 捕获)
    """
    if not filepath: filepath = f"{mode}/{site}/{filename}"
    full_path = get_file_absolute_path(filepath, site)
    if full_path:
        return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path), as_attachment=True)
    return abort(404)

@app.route('/upload_to_tos', methods=['POST'])
def upload_to_tos_route():
    """将生成的 CSV 文件上传到 TOS 对象存储，并回调业务系统通知"""
    try:
        data = request.json
        site, mode, fname = data.get('site'), data.get('mode'), data.get('filename')
        fpath = os.path.join(TMP_DIR, mode, site, fname)
        if not os.path.exists(fpath): 
            return jsonify({'status':'error', 'error':'文件不存在'}), 400

        # 上传到 TOS (TOS 需要完整的文件 Key)
        # key 示例: train/b100/quantitative/b100_xxxx.csv
        key = f"{mode}/{site}/quantitative/{fname}"
        
        with open(fpath, 'rb') as f:
            tos_client.put_object(bucket=TOS_CFG['bucket'], key=key, content=f.read())
        
        print(f"TOS 上传成功: {key}")

        # 回调业务接口通知文件已上传
        # file_abs_path 示例: tos://model-file/train/b100/quantitative
        file_abs_path = f"tos://{TOS_CFG['bucket']}/{mode}/{site}/quantitative"
        
        payload = {
            "file_abs_path": file_abs_path,
            "file_name": fname
        }
        
        upload_api_result = {} # 存储回调结果
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

        # 返回结果
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