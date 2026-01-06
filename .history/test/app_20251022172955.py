# app.py
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import pandas as pd
import numpy as np
from functools import reduce
import shutil

app = Flask(__name__)
CORS(app)

TMP_DIR = "tmp_data"
os.makedirs(TMP_DIR, exist_ok=True)

# ----------------------- 首页 -----------------------
@app.route('/')
def index():
    return render_template('index.html')

# ----------------------- 获取所有站点数据状态 -----------------------
@app.route('/get_datasets')
def get_datasets():
    all_data = []
    for site in os.listdir(TMP_DIR):
        site_path = os.path.join(TMP_DIR, site)
        if os.path.isdir(site_path):
            files = os.listdir(site_path)
            merged_files = [f for f in files if f.startswith('dataset_') and f.endswith('.csv')]
            all_data.append({
                'site_id': site,
                'merged': merged_files
            })
    return jsonify(all_data)

# ----------------------- 临时文件访问 -----------------------
@app.route('/tmp_data_preview/<filename>/<site>')
def tmp_data_preview(filename, site):
    site_path = os.path.join(TMP_DIR, site)
    path = os.path.join(site_path, filename)
    if not os.path.exists(path):
        return jsonify({'error': '文件不存在'}), 404
    try:
        df = pd.read_csv(path)
        clean_df = pd.DataFrame({
            'date': df.get('date'),
            't2m': df.get('t2m'),
            'sp': df.get('sp'),
            'rh': df.get('rh'),
            'pwv': df.get('pwv'),
            'tp': df.get('tp')
        })
        clean_df['date'] = pd.to_datetime(clean_df['date'], errors='coerce').dt.strftime('%Y/%m/%d %H:%M:%S')
        clean_df = clean_df.where(pd.notnull(clean_df), None)
        preview_rows = clean_df.head(100).to_dict(orient='records')
        return jsonify({'rows': preview_rows})
    except Exception as e:
        return jsonify({'error': f'获取详情失败: {str(e)}'}), 500

# ----------------------- 删除站点文件夹 -----------------------
@app.route('/delete_dataset/<site>', methods=['DELETE'])
def delete_dataset(site):
    site_path = os.path.join(TMP_DIR, site)
    if os.path.exists(site_path):
        shutil.rmtree(site_path)
        return jsonify({'success': True, 'message': f'{site} 已删除'})
    return jsonify({'success': False, 'error': '站点不存在'})

# ----------------------- 数据整合接口（示例，生成 dataset_*.csv） -----------------------
@app.route('/merge_datasets', methods=['POST'])
def merge_datasets():
    try:
        site_dirs = [d for d in os.listdir(TMP_DIR) if os.path.isdir(os.path.join(TMP_DIR, d))]
        results = []
        for site in site_dirs:
            site_path = os.path.join(TMP_DIR, site)
            csv_files = [os.path.join(site_path, f) for f in os.listdir(site_path) if f.endswith('.csv') and not f.startswith('dataset_')]
            if len(csv_files) < 3:
                continue
            dfs = [pd.read_csv(f) for f in csv_files]
            merged = reduce(lambda l,r: pd.merge(l,r,on='data_time',how='outer'), dfs)
            merged_path = os.path.join(site_path, f"dataset_{len([f for f in os.listdir(site_path) if f.startswith('dataset_')])+1}.csv")
            merged.to_csv(merged_path, index=False, encoding='utf-8-sig')
            results.append({'site_id': site, 'dataset': os.path.basename(merged_path)})
        if not results:
            return jsonify({'error': '没有站点合并成功'}), 400
        return jsonify({'status':'success','results':results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ----------------------- 启动 -----------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
