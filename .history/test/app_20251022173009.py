# app.py
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import pandas as pd
import numpy as np
from functools import reduce
import shutil
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# ----------------------- 临时数据目录 -----------------------
TMP_DIR = "tmp_data"
os.makedirs(TMP_DIR, exist_ok=True)

# ----------------------- 首页 -----------------------
@app.route('/')
def index():
    return render_template('index.html')

# ----------------------- 下载数据（示例，无数据库，生成随机数据） -----------------------
@app.route('/download_data', methods=['POST'])
def download_data():
    data = request.json
    data_type = data.get('type')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    device = data.get('device') or data.get('station_id')
    if not all([data_type, start_time, end_time, device]):
        return jsonify({'error': '参数缺失'}), 400

    # 生成随机数据模拟下载
    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        n = min(int((end_dt-start_dt).total_seconds()//900)+1, 5000)  # 15分钟间隔
        times = [start_dt + timedelta(minutes=15*i) for i in range(n)]
        df = pd.DataFrame({'data_time': times})
        if data_type=='pwv':
            df['pwv'] = np.random.uniform(0,50,size=n).round(2)
        elif data_type=='weather':
            df['ta'] = np.random.uniform(10,35,size=n).round(2)
            df['pa'] = np.random.uniform(900,1050,size=n).round(2)
            df['ua'] = np.random.uniform(30,100,size=n).round(2)
        elif data_type=='rain':
            df['rainfall'] = np.random.uniform(0,10,size=n).round(2)
        else:
            return jsonify({'error':'数据类型错误'}), 400

        # 保存到站点文件夹
        site_dir = os.path.join(TMP_DIR, device)
        os.makedirs(site_dir, exist_ok=True)
        tmp_file = os.path.join(site_dir, f"{data_type}.csv")
        df.to_csv(tmp_file, index=False, encoding='utf-8-sig')
        return jsonify({
            'count': len(df),
            'data': df.head(100).to_dict(orient='records'),
            'tmp_file': os.path.basename(tmp_file),
            'start_time': start_dt.strftime("%Y/%m/%d %H:%M:%S"),
            'end_time': end_dt.strftime("%Y/%m/%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({'error': f'生成数据失败: {str(e)}'}), 500

# ----------------------- 数据整合 -----------------------
@app.route('/merge_datasets', methods=['POST'])
def merge_datasets():
    try:
        site_dirs = [d for d in os.listdir(TMP_DIR) if os.path.isdir(os.path.join(TMP_DIR,d))]
        results = []
        for site in site_dirs:
            site_path = os.path.join(TMP_DIR, site)
            csv_files = [os.path.join(site_path,f) for f in os.listdir(site_path) if f.endswith('.csv') and not f.startswith('dataset_')]
            if len(csv_files)<1:
                continue
            dfs=[]
            for f in csv_files:
                df = pd.read_csv(f)
                # 保留必须字段
                cols = ['data_time','ta','pa','ua','pwv','rainfall']
                valid_cols = [c for c in cols if c in df.columns]
                dfs.append(df[valid_cols])
            merged = reduce(lambda l,r: pd.merge(l,r,on='data_time',how='outer'), dfs)
            merged = merged.sort_values('data_time').reset_index(drop=True)

            # 列名映射
            col_map = {'data_time':'date','ta':'t2m','pa':'sp','ua':'rh','pwv':'pwv','rainfall':'tp'}
            for k,v in col_map.items():
                if k in merged.columns:
                    merged.rename(columns={k:v}, inplace=True)
                else:
                    merged[v]=np.nan
            merged = merged[['date','t2m','sp','rh','pwv','tp']]
            for c in ['t2m','sp','rh','pwv','tp']:
                merged[c]=pd.to_numeric(merged[c], errors='coerce').round(3)

            # 保存合并文件
            existing = [f for f in os.listdir(site_path) if f.startswith('dataset_')]
            dataset_name = f"dataset_{len(existing)+1}.csv"
            merged_path = os.path.join(site_path, dataset_name)
            merged.to_csv(merged_path,index=False,encoding='utf-8-sig')

            # 时间范围
            first_date = pd.to_datetime(merged['date'], errors='coerce').min().strftime('%Y/%m/%d %H:%M:%S')
            last_date = pd.to_datetime(merged['date'], errors='coerce').max().strftime('%Y/%m/%d %H:%M:%S')
            time_range = f"{first_date} ~ {last_date}"

            results.append({'site_id':site,'dataset':dataset_name,'time_range':time_range})
        if not results:
            return jsonify({'error':'没有站点合并成功'}),400
        return jsonify({'status':'success','results':results})
    except Exception as e:
        return jsonify({'error':str(e)}),500

# ----------------------- 获取所有站点数据 -----------------------
@app.route('/get_datasets')
def get_all_datasets():
    all_data=[]
    for site in os.listdir(TMP_DIR):
        site_path=os.path.join(TMP_DIR,site)
        if os.path.isdir(site_path):
            files = os.listdir(site_path)
            merged_files = [f for f in files if f.startswith('dataset_') and f.endswith('.csv')]
            all_data.append({'site_id':site,'merged':merged_files})
    return jsonify(all_data)

# ----------------------- 数据详情预览 -----------------------
@app.route('/tmp_data_preview/<filename>/<site>')
def tmp_data_preview(filename, site):
    site_path = os.path.join(TMP_DIR, site)
    path = os.path.join(site_path, filename)
    if not os.path.exists(path):
        return jsonify({'error':'文件不存在'}),404
    try:
        df=pd.read_csv(path)
        clean_df=pd.DataFrame({
            'date':df.get('date'),
            't2m':df.get('t2m'),
            'sp':df.get('sp'),
            'rh':df.get('rh'),
            'pwv':df.get('pwv'),
            'tp':df.get('tp')
        })
        clean_df['date']=pd.to_datetime(clean_df['date'],errors='coerce').dt.strftime('%Y/%m/%d %H:%M:%S')
        clean_df=clean_df.where(pd.notnull(clean_df),None)
        rows=clean_df.head(100).to_dict(orient='records')
        return jsonify({'rows':rows})
    except Exception as e:
        return jsonify({'error':str(e)}),500

# ----------------------- 删除站点 -----------------------
@app.route('/delete_dataset/<site>',methods=['DELETE'])
def delete_dataset(site):
    site_path = os.path.join(TMP_DIR, site)
    if os.path.exists(site_path):
        shutil.rmtree(site_path)
        return jsonify({'success':True,'message':f'{site} 已删除'})
    return jsonify({'success':False,'error':'站点不存在'})

# ----------------------- 启动 -----------------------
if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
