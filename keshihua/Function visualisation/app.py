import os
import io
import json
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
import threading
import subprocess
import time
import requests


try:
    import clickhouse_connect
except Exception:
    clickhouse_connect = None

try:
    import cdsapi
    import xarray as xr
except Exception:
    cdsapi = None
    xr = None

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), "uploads")
app.config['RESULT_FOLDER'] = os.path.abspath("results")
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

# ---------------------------
# Utilities
# ---------------------------

def json_ok(**kwargs):
    return jsonify({"ok": True, **kwargs})

def json_err(msg, **kwargs):
    return jsonify({"ok": False, "error": msg, **kwargs}), 400

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def save_upload(file_storage, subdir=""):
    ensure_dir(os.path.join(app.config['UPLOAD_FOLDER'], subdir))
    filename = secure_filename(file_storage.filename)
    full = os.path.join(app.config['UPLOAD_FOLDER'], subdir, filename)
    file_storage.save(full)
    return full

# ---------------------------
# Module 1: 设备数据下载
# ---------------------------
def device_query_and_process(start_date, end_date, devices, clickhouse_config):
    if clickhouse_connect is None:
        raise RuntimeError("clickhouse_connect 未安装或不可用")
    import csv
    import pytz
    from datetime import datetime as dt

    def convert_to_beijing_time(utc_time):
        try:
            if isinstance(utc_time, pd.Timestamp):
                utc_time = utc_time.tz_localize('UTC').tz_convert('Asia/Shanghai')
                return utc_time.strftime('%Y-%m-%d %H:%M:%S')
            try:
                dtt = dt.strptime(utc_time, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                dtt = dt.strptime(utc_time, '%Y-%m-%d %H:%M:%S')
            dtt = pytz.utc.localize(dtt).astimezone(pytz.timezone('Asia/Shanghai'))
            return dtt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"时间转换错误: {utc_time}, 错误: {e}")
            return utc_time

    end_datetime = f"{end_date} 23:59:59.999"
    outputs = []
    for device in devices:
        folder_name = os.path.join(app.config['RESULT_FOLDER'], f"{device}_raw_data_{start_date}_to_{end_date}")
        ensure_dir(folder_name)

        try:
            client = clickhouse_connect.get_client(**clickhouse_config)
            print(f"连接ClickHouse成功，开始处理设备 {device} 数据...")

            earliest_query = f"""
                SELECT min(data_time)
                FROM dwd_hws_data
                WHERE data_time >= '{start_date} 00:00:00'
                AND device = '{device}'
            """
            earliest_result = client.query(earliest_query)
            earliest_time = earliest_result.result_rows[0][0] if earliest_result.result_rows else None
            if earliest_time is None:
                print(f"设备 {device} 无数据，跳过。")
                continue
            print(f"设备 {device} 最早数据时间: {earliest_time}")
            start_datetime = earliest_time

            hws_query = f"""
                SELECT data_time, device, Pa, Rc, Ta, Ua
                FROM dwd_hws_data
                WHERE data_time BETWEEN '{start_datetime}' AND '{end_datetime}'
                AND device = '{device}'
                ORDER BY data_time
            """
            hws_result = client.query(hws_query)
            hws_df = pd.DataFrame(hws_result.result_rows, columns=hws_result.column_names)
            hws_df['data_time'] = pd.to_datetime(hws_df['data_time'])

            raw_hws_file = os.path.join(folder_name, f'dwd_hws_data_raw_{device}.csv')
            hws_df.to_csv(raw_hws_file, index=False, quoting=1)  # QUOTE_NONNUMERIC

            pwv_query = f"""
                SELECT data_time, device, pwv
                FROM dwd_pwv_data
                WHERE data_time BETWEEN '{start_datetime}' AND '{end_datetime}'
                AND device = '{device}'
                ORDER BY data_time
            """
            pwv_result = client.query(pwv_query)
            pwv_df = pd.DataFrame(pwv_result.result_rows, columns=pwv_result.column_names)
            pwv_df['data_time'] = pd.to_datetime(pwv_df['data_time'])
            raw_pwv_file = os.path.join(folder_name, f'dwd_pwv_data_raw_{device}.csv')
            pwv_df.to_csv(raw_pwv_file, index=False, quoting=1)

            predict_query = f"""
                SELECT predict_time, device, real_rainfall_transient,predict_rainfall
                FROM dwd_predict_real_data
                WHERE data_time BETWEEN '{start_datetime}' AND '{end_datetime}'
                AND device = '{device}'
                ORDER BY predict_time
            """
            predict_result = client.query(predict_query)
            predict_df = pd.DataFrame(predict_result.result_rows, columns=predict_result.column_names)
            predict_df['predict_time'] = pd.to_datetime(predict_df['predict_time'])
            raw_predict_file = os.path.join(folder_name, f'dwd_predict_real_data_raw_{device}.csv')
            predict_df.to_csv(raw_predict_file, index=False, quoting=1)

            def get_closest_records(df, dev):
                target_minutes = [0, 15, 30, 45]
                df = df[df['device'] == dev].copy()
                df = df.sort_values('data_time')
                df['hour'] = df['data_time'].dt.floor('h')
                closest_rows = []
                for hour in df['hour'].unique():
                    df_hour = df[df['hour'] == hour].copy()
                    for m in target_minutes:
                        target_time = hour + pd.Timedelta(minutes=m)
                        if df_hour.empty:
                            continue
                        df_hour['time_diff'] = (df_hour['data_time'] - target_time).abs()
                        idx_min = df_hour['time_diff'].idxmin()
                        closest_row = df_hour.loc[idx_min].copy()
                        closest_row['data_time'] = target_time
                        closest_rows.append(closest_row)
                closest_df = pd.DataFrame(closest_rows)
                return closest_df.drop(columns=['hour', 'time_diff'], errors='ignore').sort_values('data_time').reset_index(drop=True)

            hws_closest = get_closest_records(hws_df, device)
            pwv_closest = get_closest_records(pwv_df, device)

            merged_df = pd.merge(
                hws_closest,
                pwv_closest[['data_time', 'pwv']],
                on='data_time',
                how='inner'
            )

            merged_df = merged_df.rename(columns={
                'data_time': 'date',
                'Pa': 'sp',
                'Rc': 'tp',
                'Ta': 't2m',
                'Ua': 'rh'
            })

            predict_df = predict_df.rename(columns={'predict_time': 'date'})
            predict_df['date'] = pd.to_datetime(predict_df['date'])
            merged_df['date'] = pd.to_datetime(merged_df['date'])

            merged_df = pd.merge(
                merged_df,
                predict_df[['date', 'real_rainfall_transient']],
                on='date',
                how='left'
            )
            merged_df['tp'] = merged_df['real_rainfall_transient'].fillna(0)
            merged_df.drop(columns=['real_rainfall_transient'], inplace=True)

            final_cols = ['date', 't2m', 'sp', 'rh', 'pwv', 'tp']
            merged_df = merged_df[final_cols]
            output_file = os.path.join(folder_name, f'dwd_hws_data_{device}_result.csv')
            merged_df.to_csv(output_file, index=False, quoting=1)

            outputs.append({
                "device": device,
                "folder": folder_name,
                "files": [
                    os.path.basename(raw_hws_file),
                    os.path.basename(raw_pwv_file),
                    os.path.basename(raw_predict_file),
                    os.path.basename(output_file),
                ]
            })

        except Exception as e:
            traceback.print_exc()
            outputs.append({"device": device, "error": str(e)})

    return outputs


@app.post("/api/device-download")
def api_device_download():
    data = request.get_json(force=True)
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    devices = data.get("devices", [])
    ch_cfg = data.get("clickhouse_config", {
        'host': 'bytehouse.huoshan.accurain.cn',
        'port': 80,
        'username': 'accurain_guest',
        'password': 'V3VuWS7%FWs@u',
        'database': 'accurain'
    })
    if not start_date or not end_date or not devices:
        return json_err("缺少必要参数：start_date/end_date/devices")
    try:
        outputs = device_query_and_process(start_date, end_date, devices, ch_cfg)
        return json_ok(results=outputs)
    except Exception as e:
        return json_err(str(e))


# ---------------------------
# Module 2: 荆楚水库数据处理
# ---------------------------

def jingchu_process(input_folder, data_folder, pred_folder, output_folder):
    from datetime import timedelta
    ensure_dir(pred_folder)
    ensure_dir(output_folder)

    def standardize_columns(df):
        df = df.rename(columns={'时间': 'time','时段雨量': 'rainfall'})
        if '累计雨量' in df.columns:
            df = df.drop(columns=['累计雨量'])
        return df

    def expand_and_fill_rainfall(df):
        df = df.sort_values('time').reset_index(drop=True)
        full_time_range = pd.date_range(start=df['time'].min(), end=df['time'].max(), freq='h')
        full_df = pd.DataFrame({'time': full_time_range})
        merged_df = pd.merge(full_df, df, on='time', how='left')
        merged_df['rainfall'] = merged_df['rainfall'].fillna(0)

        expanded_data = []
        for _, row in merged_df.iterrows():
            current_time = row['time']
            rainfall = row['rainfall']
            for j in range(3, -1, -1):
                new_time = current_time - timedelta(minutes=15 * j)
                expanded_data.append({'time': new_time, 'rainfall': rainfall / 4.0})
        result_df = pd.DataFrame(expanded_data)
        result_df = result_df.sort_values('time').reset_index(drop=True)
        result_df['time'] = result_df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        return result_df

    logs = []

    for filename in os.listdir(input_folder):
        if not filename.lower().endswith('.xlsx'):
            continue
        file_path = os.path.join(input_folder, filename)
        df = pd.read_excel(file_path)
        if df.empty:
            logs.append(f"Warning: {filename} is empty, skipped.")
            continue
        df = standardize_columns(df)
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['time']).sort_values('time').reset_index(drop=True)
        if df.empty:
            logs.append(f"Warning: {filename} is empty after parsing time, skipped.")
            continue
        if df.iloc[0]['time'].hour == 0 and df.iloc[0]['time'].minute == 0:
            df = df.iloc[1:].reset_index(drop=True)

        result = expand_and_fill_rainfall(df)
        output_csv = os.path.join(pred_folder, filename.replace('.xlsx', '.csv'))
        result.to_csv(output_csv, index=False)
        logs.append(f"Saved expanded CSV: {output_csv}")

    for file in os.listdir(pred_folder):
        if not file.lower().endswith(".csv"):
            continue
        device_name = file.replace(".csv", "")
        device_id = device_name.lower()

        raw_folder_prefix = f"{device_id}_raw_data_"
        matched_folders = [f for f in os.listdir(data_folder) if f.startswith(raw_folder_prefix)]
        if not matched_folders:
            logs.append(f"未找到 {device_id} 对应的 raw_data 文件夹，跳过。")
            continue

        raw_folder = os.path.join(data_folder, matched_folders[0])
        raw_csv = os.path.join(raw_folder, f"dwd_hws_data_{device_id}_result.csv")
        if not os.path.exists(raw_csv):
            logs.append(f"文件不存在：{raw_csv}，跳过")
            continue

        df_main = pd.read_csv(raw_csv)
        if 'date' not in df_main.columns or 'tp' not in df_main.columns:
            logs.append(f"{raw_csv} 缺少必要字段，跳过")
            continue

        df_ref = pd.read_csv(os.path.join(pred_folder, file))
        if 'time' not in df_ref.columns or 'rainfall' not in df_ref.columns:
            logs.append(f"{file} 缺少必要字段，跳过")
            continue

        df_main['date'] = pd.to_datetime(df_main['date'])
        df_ref['time'] = pd.to_datetime(df_ref['time'])

        df_merged = pd.merge(df_main, df_ref[['time', 'rainfall']],
                             left_on='date', right_on='time', how='left')

        df_merged['tp'] = df_merged['rainfall'].fillna(0)
        df_merged.drop(columns=['rainfall', 'time'], inplace=True)

        output_path = os.path.join(output_folder, f"{device_id}.csv")
        df_merged.to_csv(output_path, index=False)
        logs.append(f"已保存：{output_path}")

    return logs

@app.post("/api/jingchu-process")
def api_jingchu_process():
    data = request.get_json(force=True)
    input_folder = data.get("input_folder", "./jingchu_data/8month")
    data_folder = data.get("data_folder", "./jingchu_data/data_8month")
    pred_folder = data.get("pred_folder", "./jingchu_data/jingchu_result_8month")
    output_folder = data.get("output_folder", "./jingchu_data/device_data_8")

    # 确保文件夹存在
    for folder in [input_folder, data_folder, pred_folder, output_folder]:
        os.makedirs(folder, exist_ok=True)

    # normalize to absolute in results
    input_folder = os.path.abspath(input_folder)
    data_folder = os.path.abspath(data_folder)
    pred_folder = os.path.abspath(pred_folder)
    output_folder = os.path.abspath(output_folder)
    ensure_dir(pred_folder); ensure_dir(output_folder)

    try:
        logs = jingchu_process(input_folder, data_folder, pred_folder, output_folder)
        return json_ok(logs=logs, pred_folder=pred_folder, output_folder=output_folder)
    except Exception as e:
        traceback.print_exc()
        return json_err(str(e))


# ---------------------------
# Module 3: ERA5 下载与处理
# ---------------------------

def era5_download_and_process(device, start_year, start_month, end_year, end_month, target_lat, target_lon, area):
    if cdsapi is None or xr is None:
        raise RuntimeError("cdsapi/xarray 未安装或不可用，请在部署环境安装，并配置 ~/.cdsapirc")
    import pandas as pd

    def download_month_data(year, month, target_lat, target_lon, area):
        output_dir = os.path.join(app.config['RESULT_FOLDER'], "nc", f"{device}")
        ensure_dir(output_dir)
        output_filename = os.path.join(output_dir, f"era5_data_{year}_{str(month).zfill(2)}.nc")

        if month == 2:
            days = 28
        elif month in [4, 6, 9, 11]:
            days = 30
        else:
            days = 31
        day_list = [str(d).zfill(2) for d in range(1, days + 1)]

        if not os.path.exists(output_filename):
            request = {
                "variable": [
                    "total_precipitation",
                    "2m_temperature",
                    "surface_pressure",
                    "2m_dewpoint_temperature"
                ],
                "year": str(year),
                "month": [str(month).zfill(2)],
                "day": day_list,
                "time": [f"{h:02d}:00" for h in range(24)],
                "data_format": "netcdf",
                "download_format": "unarchived",
                "area": area
            }
            client = cdsapi.Client()
            client.retrieve("reanalysis-era5-land", request, output_filename)
        return output_filename

    def process_month_data(filename, year, month, target_lat, target_lon):
        ds = xr.open_dataset(filename)

        if month == 2:
            days = 28
        elif month in [4, 6, 9, 11]:
            days = 30
        else:
            days = 31

        start_date = f"{year}-{str(month).zfill(2)}-01"
        end_date = f"{year}-{str(month).zfill(2)}-{days}"
        time_slice = slice(start_date, end_date)

        variables = {
            'tp': 'total_precipitation',
            't2m': '2m_temperature',
            'sp': 'surface_pressure',
            'd2m': '2m_dewpoint_temperature'
        }

        df = pd.DataFrame()
        for var, name in variables.items():
            time_filtered = ds[var].sel(valid_time=time_slice)
            data = time_filtered.sel(latitude=target_lat, longitude=target_lon, method='nearest')
            temp_df = data.to_dataframe(name=name).reset_index()
            if df.empty:
                df = temp_df[['valid_time', name]]
            else:
                df = pd.merge(df, temp_df[['valid_time', name]], on='valid_time')

        df['temp_c'] = df['2m_temperature'] - 273.15
        df['dewpoint_c'] = df['2m_dewpoint_temperature'] - 273.15

        df['rh'] = 100 * np.exp(
            (17.269 * df['dewpoint_c']) / (237.3 + df['dewpoint_c']) -
            (17.269 * df['temp_c']) / (237.3 + df['temp_c'])
        ).clip(0, 100)

        df['e'] = 6.112 * np.exp((17.67 * df['dewpoint_c']) / (df['dewpoint_c'] + 243.5))
        df['pwv'] = (0.14 * df['e'] * (df['surface_pressure'] / 100)) / (df['temp_c'] + 273.15)
        df['pwv'] = df['pwv'].clip(0, 100)

        df['tp'] = (df['total_precipitation'] * 1000).diff().fillna(0).clip(lower=0)
        df['pressure'] = df['surface_pressure'] / 100
        df['date'] = df['valid_time'] + pd.Timedelta(hours=8)

        final_df = pd.DataFrame({
            'date': df['date'],
            't2m': df['temp_c'],
            'sp': df['pressure'],
            'rh': df['rh'],
            'pwv': df['pwv'],
            'tp': df['tp']
        })
        return final_df

    output_csv = os.path.join(app.config['RESULT_FOLDER'], "六要素数据")
    ensure_dir(output_csv)
    output_csv = os.path.join(output_csv, f"{device}.csv")

    all_data = pd.DataFrame()
    for year in range(start_year, end_year + 1):
        start_m = start_month if year == start_year else 1
        end_m = end_month if year == end_year else 12
        for month in range(start_m, end_m + 1):
            fn = download_month_data(year, month, target_lat, target_lon, area)
            month_df = process_month_data(fn, year, month, target_lat, target_lon)
            all_data = pd.concat([all_data, month_df], ignore_index=True)

    all_data = all_data.sort_values('date')
    all_data['date'] = pd.to_datetime(all_data['date'])
    all_data.set_index('date', inplace=True)
    new_index = pd.date_range(
        start=all_data.index.min() - pd.Timedelta(minutes=45),
        end=all_data.index.max(),
        freq='15min'
    )
    all_data = all_data.reindex(new_index, method='bfill')
    all_data['hour_group'] = all_data.index.floor('h')
    for col in ['tp']:
        all_data[col] = all_data.groupby('hour_group')[col].transform(lambda x: x / 4)
    all_data = all_data.drop(columns=['hour_group']).reset_index().rename(columns={'index':'date'})
    all_data.to_csv(output_csv, index=False)

    return output_csv

@app.post("/api/era5-download")
def api_era5_download():
    data = request.get_json(force=True)
    device = data.get("device", "B139")
    start_year = int(data.get("start_year", 2025))
    start_month = int(data.get("start_month", 5))
    end_year = int(data.get("end_year", 2025))
    end_month = int(data.get("end_month", 7))
    target_lat = float(data.get("target_lat", 31.39))
    target_lon = float(data.get("target_lon", 115.04))
    area = data.get("area", [31.40, 114.24, 29.45, 116.07])

    try:
        out_csv = era5_download_and_process(device, start_year, start_month, end_year, end_month, target_lat, target_lon, area)
        return json_ok(file=out_csv)
    except Exception as e:
        traceback.print_exc()
        return json_err(str(e))


# ---------------------------
# Module 4: R2 / RMSE 计算
# ---------------------------

from sklearn.metrics import r2_score, mean_squared_error

def calc_metrics(csv_path, start_date=None, end_date=None):
    df = pd.read_csv(csv_path)
    # 列：'时间','实测雨量','预测雨量'
    if '时间' not in df.columns:
        if 'date' in df.columns:
            df.rename(columns={'date': '时间'}, inplace=True)
        else:
            raise ValueError("缺少列：时间 / date")
    if '实测雨量' not in df.columns or '预测雨量' not in df.columns:
        if 'true' in df.columns and 'pred' in df.columns:
            df.rename(columns={'true':'实测雨量','pred':'预测雨量'}, inplace=True)
        else:
            raise ValueError("缺少列：实测雨量/预测雨量 或 true/pred")

    def convert_time(time_str):
        try:
            time_str = str(time_str).replace('年', '/').replace('月', '/').replace('日', '')
            for fmt in ['%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M', '%Y/%m/%d %H', '%Y-%m-%d %H', '%Y-%m-%d %H:%M:%S']:
                try:
                    return pd.to_datetime(time_str, format=fmt)
                except:
                    continue
            return pd.to_datetime(time_str)
        except:
            return pd.NaT

    df['时间'] = df['时间'].apply(convert_time)
    df.dropna(subset=['时间'], inplace=True)

    merged = df.sort_values('时间').set_index('时间')
    full_index = pd.date_range(start=merged.index.min(), end=merged.index.max(), freq='h')
    merged = merged.reindex(full_index)
    merged.index.name = '时间'

    numeric_cols = ['实测雨量', '预测雨量']
    for col in numeric_cols:
        if col in merged.columns:
            merged[col] = merged[col].interpolate(method='time').ffill().bfill()

    merged = merged.reset_index()
    valid_data = merged.dropna(subset=numeric_cols, how='any')

    if start_date and end_date:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        valid_data = valid_data[(valid_data['时间'] >= start_dt) & (valid_data['时间'] <= end_dt)]

    y_true = valid_data['实测雨量'].values
    y_pred = valid_data['预测雨量'].values
    r2 = float(r2_score(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))

    return {
        "start": valid_data['时间'].min().strftime('%Y-%m-%d %H:%M') if not valid_data.empty else None,
        "end": valid_data['时间'].max().strftime('%Y-%m-%d %H:%M') if not valid_data.empty else None,
        "count": int(len(valid_data)),
        "r2": r2,
        "rmse": rmse
    }

@app.post("/api/metrics")
def api_metrics():
    if request.content_type and "multipart/form-data" in request.content_type:
        file = request.files.get("file")
        if not file:
            return json_err("未收到文件")
        path = save_upload(file, subdir="metrics")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
    else:
        data = request.get_json(force=True)
        path = data.get("csv_path")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if not path:
            return json_err("缺少 csv_path 或上传文件")

    try:
        res = calc_metrics(path, start_date, end_date)
        return json_ok(**res, csv_path=path)
    except Exception as e:
        traceback.print_exc()
        return json_err(str(e))


# ---------------------------
# Module 5: 月度数据合并
# ---------------------------

def merge_months(folder_5_6, folder_7, folder_8, output_folder):
    ensure_dir(output_folder)
    files_56 = set(os.listdir(folder_5_6)) if os.path.isdir(folder_5_6) else set()
    files_7 = set(os.listdir(folder_7)) if os.path.isdir(folder_7) else set()
    files_8 = set(os.listdir(folder_8)) if os.path.isdir(folder_8) else set()
    all_files = files_56.union(files_7).union(files_8)

    logs = [f"找到 {len(all_files)} 个文件"]
    outputs = []

    for filename in all_files:
        dfs = []
        for folder in [folder_5_6, folder_7, folder_8]:
            if filename in (files_56 if folder==folder_5_6 else files_7 if folder==folder_7 else files_8):
                dfs.append(pd.read_csv(os.path.join(folder, filename), sep=","))

        if not dfs:
            continue

        dfs = [df.dropna(axis=1, how='all') for df in dfs if not df.empty]
        if dfs:
            df_all = pd.concat(dfs, ignore_index=True)
        else:
            df_all = pd.DataFrame()

        df_all = pd.concat(dfs, ignore_index=True)
        if "date" in df_all.columns:
            df_all["date"] = pd.to_datetime(df_all["date"])
            df_all = df_all.sort_values(by="date").reset_index(drop=True)
            df_all = df_all.drop_duplicates(subset="date", keep="first")

        out_path = os.path.join(output_folder, filename)
        df_all.to_csv(out_path, index=False, encoding="utf-8")
        outputs.append(out_path)

    return logs, outputs


@app.route("/api/merge-months", methods=["POST"])
def api_merge_months():
    data = request.get_json(force=True)
    folder_5_6 = data.get("folder_5_6", "./merge_month/5-6-extracted_files")
    folder_7 = data.get("folder_7", "./merge_month/7-extracted_files")
    folder_8 = data.get("folder_8", "./merge_month/8-extracted_files")
    output_folder = data.get("output_folder", "./merge_month/5-8-merged_files")

    folder_5_6 = os.path.abspath(folder_5_6)
    folder_7 = os.path.abspath(folder_7)
    folder_8 = os.path.abspath(folder_8)
    output_folder = os.path.abspath(output_folder)

    ensure_dir(output_folder)
    try:
        logs, outputs = merge_months(folder_5_6, folder_7, folder_8, output_folder)
        return json_ok(logs=logs, outputs=outputs, output_folder=output_folder)
    except Exception as e:
        traceback.print_exc()
        return json_err(str(e))


# ---------------------------
# Module 6: 可视化页面
# ---------------------------

@app.get("/visualize")
def visualize_page():
    return render_template("visualize.html")

# 首页
@app.get("/")
def home():
    return render_template("index.html")

def open_browser_and_monitor():
    browser_proc = subprocess.Popen(["start", "msedge", "http://127.0.0.1:8000"], shell=True)
    try:
        while True:
            if browser_proc.poll() is not None:
                print("浏览器已关闭，尝试停止 Flask 服务...")
                try:
                    requests.get("http://127.0.0.1:8000/shutdown")
                except Exception:
                    pass
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass

@app.route("/shutdown", methods=["GET"])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return "无法获取 shutdown 函数"
    func()
    return "Flask 服务已关闭"

if __name__ == "__main__":
    threading.Thread(target=open_browser_and_monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)