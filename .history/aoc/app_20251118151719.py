from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import clickhouse_connect
from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
import traceback
import re
from urllib.parse import unquote

app = Flask(__name__)
CORS(app)

# --- 配置 ---
TMP_DIR = "tmp_data"
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

TABLE_CONFIG = {
    'pwv': {'table': 'ods_pwv_external', 'fields': ['data_time','device','pwv','data_type']},
    'weather': {'table': 'ods_hws_external', 'fields': ['data_time','device','ta','pa','ua','data_type']},
    'rain': {'table': 'ods_raingauge_external', 'fields': ['data_time','device','rainfall','data_type']}
}

DEFAULT_SOURCE_PRIORITY = ['deviced', 'cros', 'ec', 'era5']
MAX_DOWNLOAD_ROWS = 100000

# --- 工具函数 ---
def to_utc(dt_str):
    """北京时间转 UTC"""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt - timedelta(hours=8)
    except:
        return None

def find_time_col(df):
    """查找时间列"""
    for col in df.columns:
        if col.lower() in ['data_time','date','time'] or '时间' in col:
            return col
    return None

def map_column(df, target, candidates):
    """从候选列映射到目标列"""
    for col in df.columns:
        if col.lower() in [c.lower() for c in candidates]:
            return pd.to_numeric(df[col], errors='coerce')
    return pd.Series([np.nan]*len(df))

def get_site_file(site, filename, mode=None):
    """获取站点文件绝对路径"""
    if mode:
        return os.path.join(TMP_DIR, site, mode, filename)
    return os.path.join(TMP_DIR, site, filename)

# --- 首页 ---
@app.route('/')
def index():
    return render_template('index.html')

# --- 上传 ---
@app.route('/upload_data', methods=['POST'])
def upload_data():
    try:
        if 'file' not in request.files:
            return jsonify({'error':'未检测到文件'}),400
        file = request.files['file']
        dtype = request.form.get('type')
        device = request.form.get('device') or request.form.get('station_id')
        if not device:
            return jsonify({'error':'设备/站点参数缺失'}),400

        filename = secure_filename(file.filename)
        site_dir = os.path.join(TMP_DIR, device)
        os.makedirs(site_dir, exist_ok=True)
        save_path = os.path.join(site_dir, filename)
        file.save(save_path)

        start_time = end_time = None
        try:
            df_head = pd.read_csv(save_path, encoding='utf-8-sig', nrows=10000)
            time_col = find_time_col(df_head)
            if time_col:
                dt = pd.to_datetime(pd.read_csv(save_path, usecols=[time_col])[time_col], errors='coerce')
                if dt.notna().any():
                    start_time = dt.min().strftime('%Y/%m/%d %H:%M:%S')
                    end_time = dt.max().strftime('%Y/%m/%d %H:%M:%S')
        except:
            pass

        inserted_count = 0
        if dtype in TABLE_CONFIG:
            try:
                df = pd.read_csv(save_path, encoding='utf-8-sig')
                time_col = find_time_col(df)
                if not time_col:
                    return jsonify({'status':'success','tmp_file':filename,'start_time':start_time,'end_time':end_time,'inserted_count':0,'error':'无时间列'})
                
                cfg = TABLE_CONFIG[dtype]
                insert_df = pd.DataFrame()
                insert_df['data_time'] = pd.to_datetime(df[time_col], errors='coerce')
                insert_df['device'] = df['device'].astype(str) if 'device' in df.columns else device

                col_map_basic = {
                    'pwv':['pwv','PWV','PwV'],
                    'ta':['ta','t2m','T','temp','temperature'],
                    'pa':['pa','sp','pressure'],
                    'ua':['ua','rh','humidity'],
                    'rainfall':['rain','rainfall','tp','precip']
                }
                for f in cfg['fields']:
                    if f not in ['data_time','device','data_type']:
                        insert_df[f] = map_column(df, f, col_map_basic.get(f, []))
                insert_df['data_type'] = df['data_type'].astype(str) if 'data_type' in df.columns else 'uploaded'

                insert_df = insert_df.dropna(subset=['data_time'])
                if insert_df.empty:
                    inserted_count = 0
                else:
                    # 去重
                    min_t, max_t = insert_df['data_time'].min(), insert_df['data_time'].max()
                    try:
                        q = f"""
                        SELECT data_time FROM {cfg['table']}
                        WHERE device='{device}'
                          AND data_time>=toDateTime('{(min_t - timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
                          AND data_time<=toDateTime('{(max_t + timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
                        """
                        res = client.query(q)
                        existing_times = {r[0].strftime("%Y-%m-%d %H:%M:%S") if isinstance(r[0], datetime) else str(r[0]) for r in res.result_rows}
                    except:
                        existing_times = set()

                    to_insert_df = insert_df[insert_df['data_time'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") not in existing_times)]
                    if not to_insert_df.empty:
                        to_insert_df['data_time'] = to_insert_df['data_time'].dt.strftime("%Y-%m-%d %H:%M:%S")
                        records = to_insert_df.to_dict(orient='records')
                        try:
                            client.insert(cfg['table'], records, column_names=cfg['fields'])
                            inserted_count = len(records)
                        except:
                            inserted_count = 0
            except:
                inserted_count = 0

        return jsonify({'status':'success','tmp_file':filename,'start_time':start_time,'end_time':end_time,'inserted_count':inserted_count})
    except Exception as e:
        return jsonify({'error':str(e),'trace':traceback.format_exc()}),500

# --- 单文件下载 ---
@app.route('/download_data', methods=['POST'])
def download_data():
    data = request.json
    dtype = data.get('type')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    device = data.get('device') or data.get('station_id')
    if not all([dtype,start_time,end_time,device]): return jsonify({'error':'参数缺失'}),400
    cfg = TABLE_CONFIG.get(dtype)
    if not cfg: return jsonify({'error':'数据类型错误'}),400

    start_utc, end_utc = to_utc(start_time), to_utc(end_time)
    if not all([start_utc,end_utc]): return jsonify({'error':'时间格式错误'}),400

    merged_data = {}
    for source in DEFAULT_SOURCE_PRIORITY:
        fields = ','.join(cfg['fields'])
        query = f"""
        SELECT {fields} FROM {cfg['table']}
        WHERE device='{device}'
          AND data_time>=toDateTime('{start_utc.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
          AND data_time<=toDateTime('{end_utc.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
          AND LOWER(data_type)='{source.lower()}'
        ORDER BY data_time ASC LIMIT 50000
        """
        try:
            res = client.query(query)
            for row in res.result_rows:
                t = row[0]; t_str = (t+timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") if isinstance(t,datetime) else str(t)
                if t_str not in merged_data:
                    row_dict = dict(zip(res.column_names, row))
                    if isinstance(row_dict['data_time'], datetime):
                        row_dict['data_time'] = (row_dict['data_time'] + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                    merged_data[t_str] = row_dict
        except Exception as e:
            return jsonify({'error':f'查询失败: {str(e)}'}),500

    if not merged_data: return jsonify({'error':'无数据可用'}),404
    data_list = [merged_data[k] for k in sorted(merged_data.keys())]

    site_dir = os.path.join(TMP_DIR, device)
    os.makedirs(site_dir, exist_ok=True)
    start_str = start_utc.strftime("%Y-%m-%d_%H-%M-%S")
    end_str = end_utc.strftime("%Y-%m-%d_%H-%M-%S")
    tmp_file_name = f"{dtype}_{start_str}_{end_str}.csv"
    tmp_file_path = os.path.join(site_dir,tmp_file_name)
    pd.DataFrame(data_list).to_csv(tmp_file_path,index=False,encoding='utf-8-sig')

    return jsonify({'count':len(data_list),'data':data_list[:1000],'tmp_file':tmp_file_name})

# --- 单站点批量下载辅助 ---
def _download_single_type_for_device(device,dtype,start_time,end_time,priority,mode='train'):
    cfg = TABLE_CONFIG.get(dtype)
    if not cfg: return {'type':dtype,'count':-1,'error':'未知数据类型'}
    start_utc, end_utc = to_utc(start_time), to_utc(end_time)
    if not all([start_utc,end_utc]): return {'type':dtype,'count':-1,'error':'时间格式错误'}

    merged_data = {}
    for source in priority:
        fields = ','.join(cfg['fields'])
        query = f"""
        SELECT {fields} FROM {cfg['table']}
        WHERE device='{device}'
          AND data_time>=toDateTime('{start_utc.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
          AND data_time<=toDateTime('{end_utc.strftime("%Y-%m-%d %H:%M:%S")}', 'UTC')
          AND LOWER(data_type)='{source.lower()}'
        ORDER BY data_time ASC LIMIT {MAX_DOWNLOAD_ROWS}
        """
        try:
            res = client.query(query)
            for row in res.result_rows:
                t = row[0]; t_str = (t+timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") if isinstance(t,datetime) else str(t)
                if t_str not in merged_data:
                    row_dict = dict(zip(res.column_names,row))
                    if isinstance(row_dict['data_time'],datetime):
                        row_dict['data_time'] = (row_dict['data_time'] + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                    merged_data[t_str] = row_dict
        except Exception as e:
            return {'type':dtype,'count':-1,'error':f'查询失败:{str(e)}'}

    if not merged_data: return {'type':dtype,'count':0,'tmp_file':None}
    data_list = [merged_data[k] for k in sorted(merged_data.keys())]

    site_dir = os.path.join(TMP_DIR, device, mode)
    os.makedirs(site_dir, exist_ok=True)
    start_str = start_utc.strftime("%Y-%m-%d_%H-%M-%S")
    end_str = end_utc.strftime("%Y-%m-%d_%H-%M-%S")
    tmp_file_name = f"{dtype}_{start_str}_{end_str}.csv"
    tmp_file_path = os.path.join(site_dir,tmp_file_name)
    pd.DataFrame(data_list).to_csv(tmp_file_path,index=False,encoding='utf-8-sig')

    return {'type':dtype,'count':len(data_list),'tmp_file':tmp_file_name}

# --- 批量下载 ---
@app.route('/batch_download',methods=['POST'])
def batch_download():
    try:
        data = request.json or {}
        types = data.get('types') or []
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        devices = data.get('devices') or ([data.get('device')] if data.get('device') else [])
        priority = [p.lower() for p in (data.get('priority') or DEFAULT_SOURCE_PRIORITY)]
        mode = (data.get('mode') or 'train').lower()
        if not all([types,start_time,end_time,devices]): return jsonify({'error':'参数缺失'}),400

        overall_results=[]
        for dev in devices:
            dev_res=[]
            for t in types:
                dev_res.append(_download_single_type_for_device(dev,t,start_time,end_time,priority,mode))
            overall_results.append({'device':dev,'results':dev_res})

        merged = merge_datasets_inner(devices,mode)
        return jsonify({'status':'success','details':overall_results,'merged':merged})
    except Exception as e:
        return jsonify({'error':str(e),'trace':traceback.format_exc()}),500

# --- 合并数据 ---
@app.route('/merge_datasets',methods=['POST'])
def merge_datasets():
    try:
        data = request.json or {}
        sites = data.get('sites',[])
        mode = (data.get('mode') or 'train').lower()
        if not sites: return jsonify({'success':False,'msg':'请选择站点'}),400
        merged = merge_datasets_inner(sites,mode)
        return jsonify({'success':True,'msg':'合并完成','merged':merged})
    except Exception as e:
        return jsonify({'success':False,'msg':str(e),'trace':traceback.format_exc()}),500

# --- 获取站点数据集列表 ---
@app.route('/get_datasets')
def get_datasets_route():
    site = request.args.get('site')
    if not site:
        sites = [d for d in os.listdir(TMP_DIR) if os.path.isdir(os.path.join(TMP_DIR,d))]
        return jsonify([{'site_id':s} for s in sites])
    site = site.strip()
    site_dir = os.path.join(TMP_DIR,site)
    if not os.path.exists(site_dir): return jsonify({"train":[],"pred":[]})

    def list_mode_files(mode):
        out=[]
        mode_dir=os.path.join(site_dir,mode)
        if os.path.exists(mode_dir):
            for f in os.listdir(mode_dir):
                if f.lower().endswith('.csv') and (re.match(r'^dataset[-_]',f,re.I) or re.match(r'^[A-Za-z0-9]+_\d{8}_\d{8}\.csv$',f)):
                    path = os.path.join(mode,f)
                    try:
                        df = pd.read_csv(os.path.join(site_dir,path))
                        tcol = find_time_col(df)
                        start_time = str(pd.to_datetime(df[tcol],errors='coerce').min()) if tcol else None
                        end_time = str(pd.to_datetime(df[tcol],errors='coerce').max()) if tcol else None
                    except:
                        start_time=end_time=None
                    out.append({'sub_dir':mode,'name':f,'site':site,'site_name':f"站点{site}",
                                'start_time':start_time,'end_time':end_time,
                                'created_at':time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(os.path.getctime(os.path.join(mode_dir,f)))),
                                'path':path})
        out.sort(key=lambda x: os.path.getctime(os.path.join(site_dir,x['path'])),reverse=True)
        return out

    return jsonify({"train":list_mode_files("train"),"pred":list_mode_files("pred")})

# --- 删除文件 ---
@app.route('/delete_dataset/<path:filename>/<site>',methods=['DELETE'])
def delete_dataset(filename,site):
    filename = unquote(filename)
    fpath = get_site_file(site,filename)
    if not os.path.exists(fpath): return jsonify({'status':'error','message':f'{filename}不存在'})
    try:
        os.remove(fpath)
        return jsonify({'status':'success'})
    except Exception as e:
        return jsonify({'status':'error','message':str(e)})

# --- 文件预览 ---
@app.route('/tmp_data_preview/<path:filename>/<site>')
def tmp_data_preview(filename,site):
    path = get_site_file(site,filename)
    if not os.path.exists(path): return jsonify({'error':'文件不存在'}),404
    try:
        df = pd.read_csv(path)
        def pick(col):
            for s in ['', '_x','_y']:
                if col+s in df.columns: return df[col+s]
            for c in df.columns:
                if c.lower() == col.lower(): return df[c]
            return pd.Series([None]*len(df))
        clean_df = pd.DataFrame({
            'date': pick('date') if 'date' in df.columns else pick('data_time'),
            't2m': pick('t2m'),
            'sp': pick('sp'),
            'rh': pick('rh'),
            'pwv': pick('pwv'),
            'tp': pick('tp')
        })
        clean_df['date'] = pd.to_datetime(clean_df['date'],errors='coerce').dt.strftime('%Y/%m/%d %H:%M:%S')
        clean_df = clean_df.where(pd.notnull(clean_df), None)
        return jsonify({'rows':clean_df.head(100).to_dict(orient='records')})
    except Exception as e:
        return jsonify({'error':f'获取详情失败:{str(e)}'},500)

# --- 临时文件访问 ---
@app.route('/tmp/<path:path>/<site>')
def tmp_file(path,site):
    fpath = get_site_file(site,path)
    if os.path.exists(fpath):
        return send_from_directory(os.path.dirname(fpath),os.path.basename(fpath),as_attachment=True)
    return jsonify({'error':'文件不存在'}),404

# --- 内部合并函数 ---
def merge_datasets_inner(sites,mode='train'):
    results=[]
    for site in sites:
        site_path = os.path.join(TMP_DIR,site,mode)
        if not os.path.exists(site_path): continue
        csvs=[f for f in os.listdir(site_path) if f.lower().endswith('.csv')]
        if not csvs: continue
        merged_name = f"{site}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        merged_path = os.path.join(site_path,merged_name)
        try:
            df_list=[pd.read_csv(os.path.join(site_path,f)) for f in csvs]
            df_all=pd.concat(df_list,ignore_index=True)
            df_all.to_csv(merged_path,index=False,encoding='utf-8-sig')
            results.append({'site':site,'merged_file':merged_name,'count':len(df_all)})
        except Exception as e:
            results.append({'site':site,'error':str(e)})
    return results

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
