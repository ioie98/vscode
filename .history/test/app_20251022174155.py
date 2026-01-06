from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os, pandas as pd, numpy as np
from datetime import datetime, timedelta
from functools import reduce

app = Flask(__name__)
CORS(app)

TMP_DIR = "tmp_data"
os.makedirs(TMP_DIR, exist_ok=True)

TABLE_CONFIG = {
    'pwv': ['data_time','device','pwv','data_type'],
    'weather': ['data_time','device','ta','pa','ua','data_type'],
    'rain': ['data_time','device','rainfall','data_type']
}

SOURCE_PRIORITY = ['era5','ec','cros','deviced']

def get_station_path(station):
    path = os.path.join(TMP_DIR, station)
    os.makedirs(path, exist_ok=True)
    return path

@app.route('/')
def index(): return render_template('index.html')

@app.route('/download_data', methods=['POST'])
def download_data():
    data = request.json
    data_type = data.get('type')
    device = data.get('device')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    if not all([data_type, device, start_time, end_time]):
        return jsonify({'error':'参数缺失'}),400
    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
    except:
        return jsonify({'error':'时间格式错误'}),400

    # 模拟生成数据
    dates = pd.date_range(start=start_dt,end=end_dt,freq='H')
    df = pd.DataFrame({'data_time':dates})
    if data_type=='pwv': df['pwv'] = np.random.rand(len(dates))
    elif data_type=='weather':
        df['ta']=np.random.rand(len(dates))*30
        df['pa']=np.random.rand(len(dates))*1000
        df['ua']=np.random.rand(len(dates))*100
    elif data_type=='rain': df['rainfall']=np.random.rand(len(dates))*5

    tmp_file = os.path.join(get_station_path(device), f"{data_type}_{device}.csv")
    df.to_csv(tmp_file,index=False,encoding='utf-8-sig')
    return jsonify({'count':len(df),'tmp_file':f"{device}/{os.path.basename(tmp_file)}",
                    'start_time':dates.min().strftime('%Y/%m/%d %H:%M:%S'),
                    'end_time':dates.max().strftime('%Y/%m/%d %H:%M:%S')})

@app.route('/merge_datasets', methods=['POST'])
def merge_datasets():
    data = request.json
    station = data.get('station')
    if not station: return jsonify({'error':'缺少站点'}),400
    path = get_station_path(station)
    csv_files = [os.path.join(path,f) for f in os.listdir(path) if f.endswith('.csv')]
    if len(csv_files)<3: return jsonify({'error':'数据不足'}),400

    dfs = []
    for f in csv_files:
        df = pd.read_csv(f)
        dfs.append(df)
    merged = reduce(lambda l,r: pd.merge(l,r,on='data_time',how='outer'), dfs)
    merged = merged.sort_values('data_time').reset_index(drop=True)
    col_map = {'data_time':'date','ta':'t2m','pa':'sp','ua':'rh','pwv':'pwv','rainfall':'tp'}
    for k,v in col_map.items():
        if k in merged.columns: merged[v]=merged[k]
        else: merged[v]=np.nan
    merged = merged[['date','t2m','sp','rh','pwv','tp']]
    for c in ['t2m','sp','rh','pwv','tp']: merged[c]=pd.to_numeric(merged[c],errors='coerce').round(3)

    existing = [f for f in os.listdir(path) if f.startswith('dataset_')]
    dataset_name = f"dataset_{len(existing)+1}.csv"
    merged_path = os.path.join(path,dataset_name)
    merged.to_csv(merged_path,index=False,encoding='utf-8-sig')
    first_date = pd.to_datetime(merged['date']).min().strftime('%Y/%m/%d %H:%M:%S')
    last_date = pd.to_datetime(merged['date']).max().strftime('%Y/%m/%d %H:%M:%S')
    return jsonify({'dataset':f"{station}/{dataset_name}",'time_range':f"{first_date} ~ {last_date}"})


@app.route('/tmp_data/<station>/<path:filename>')
def serve_tmp_data(station,filename):
    return send_from_directory(get_station_path(station),filename)

@app.route('/delete_dataset/<station>/<filename>',methods=['DELETE'])
def delete_dataset(station,filename):
    path = os.path.join(get_station_path(station),filename)
    if os.path.exists(path): os.remove(path); return jsonify({'success':True})
    return jsonify({'success':False,'error':'文件不存在'}),404

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
