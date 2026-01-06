# app.py
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import clickhouse_connect
from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np
from functools import reduce

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
    'pwv': {'table': 'ods_pwv_external', 'fields': ['data_time', 'device', 'pwv', 'data_type']},
    'weather': {'table': 'ods_hws_external', 'fields': ['data_time', 'device', 'ta', 'pa', 'ua', 'data_type']},
    'rain': {'table': 'ods_raingauge_external', 'fields': ['data_time', 'device', 'rainfall', 'data_type']}
}
SOURCE_PRIORITY = ['era5', 'ec', 'cros', 'deviced']

# 临时数据存储
TMP_DIR = "tmp_data"
os.makedirs(TMP_DIR, exist_ok=True)

# -----------------------
# 工具函数
# -----------------------
def get_station_path(station):
    path = os.path.join(TMP_DIR, station)
    os.makedirs(path, exist_ok=True)
    return path

# -----------------------
# 首页路由
# -----------------------
@app.route('/')
def index():
    return render_template('index.html')

# -----------------------
# 数据下载接口
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

    # 保存临时 CSV 到站点文件夹
    tmp_file = os.path.join(get_station_path(device), f"{data_type}_{device}.csv")
    pd.DataFrame(data_list).to_csv(tmp_file, index=False, encoding='utf-8-sig')

    return jsonify({
        'count': len(data_list),
        'data': data_list[:1000],
        'tmp_file': f"{device}/{os.path.basename(tmp_file)}"
    })

# -----------------------
# 数据整合接口
# -----------------------
@app.route('/merge_datasets', methods=['POST'])
def merge_datasets():
    try:
        csv_files = []
        for station_folder in os.listdir(TMP_DIR):
            station_path = os.path.join(TMP_DIR, station_folder)
            for f in os.listdir(station_path):
                if f.endswith('.csv') and not f.startswith('dataset_'):
                    csv_files.append(os.path.join(station_path, f))

        if len(csv_files) < 3:
            return jsonify({'error': '数据不足，请确保三个数据源均已下载或上传'}), 400

        dfs = []
        for f in csv_files:
            df = pd.read_csv(f)
            valid_cols = [c for c in ['data_time', 'ta', 'pa', 'ua', 'pwv', 'rainfall'] if c in df.columns]
            df = df[valid_cols]
            dfs.append(df)

        merged = reduce(lambda left, right: pd.merge(left, right, on='data_time', how='outer'), dfs)
        merged = merged.sort_values(by='data_time').reset_index(drop=True)

        col_map = {'data_time': 'date', 'ta': 't2m', 'pa': 'sp', 'ua': 'rh', 'pwv': 'pwv', 'rainfall': 'tp'}
        for k, v in col_map.items():
            if k in merged.columns:
                merged = merged.rename(columns={k: v})
            else:
                merged[v] = np.nan
        merged = merged[['date', 't2m', 'sp', 'rh', 'pwv', 'tp']]
        for col in ['t2m', 'sp', 'rh', 'pwv', 'tp']:
            if col in merged.columns:
                merged[col] = pd.to_numeric(merged[col], errors='coerce').round(3)

        existing = [f for f in os.listdir(TMP_DIR) if f.startswith('dataset_')]
        dataset_name = f"dataset_{len(existing)+1}.csv"
        merged_path = os.path.join(TMP_DIR, dataset_name)
        merged.to_csv(merged_path, index=False, encoding='utf-8-sig')

        merged['date'] = pd.to_datetime(merged['date'], errors='coerce')
        first_date = merged['date'].min().strftime('%Y/%m/%d %H:%M:%S')
        last_date = merged['date'].max().strftime('%Y/%m/%d %H:%M:%S')
        time_range = f"{first_date} ~ {last_date}"

        return jsonify({
            'status': 'success',
            'message': f'合并完成: {dataset_name}',
            'dataset': dataset_name,
            'time_range': time_range
        })
    except Exception as e:
        return jsonify({'error': f'合并失败: {str(e)}'}), 500

# -----------------------
# 临时文件访问
# -----------------------
@app.route('/tmp_data/<station>/<path:filename>')
def serve_tmp_data(station, filename):
    return send_from_directory(get_station_path(station), filename)

# -----------------------
# 删除数据集
# -----------------------
@app.route('/delete_dataset/<station>/<filename>', methods=['DELETE'])
def delete_dataset(station, filename):
    path = os.path.join(get_station_path(station), filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '文件不存在'}), 404

# -----------------------
# 数据预览接口
# -----------------------
@app.route('/tmp_data_preview/<station>/<filename>')
def tmp_data_preview(station, filename):
    path = os.path.join(get_station_path(station), filename)
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
