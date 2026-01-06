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
import pytz
import calendar


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
import os, csv, pandas as pd, pytz, clickhouse_connect
from datetime import datetime, timedelta

def safe_folder_name(name):
    return name.replace(':','-').replace(' ','_')

def beijing_to_utc(date_str: str) -> str:
    try:
        # 这里要匹配完整的 "YYYY-MM-DD HH:MM:SS"
        dt_beijing = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        # 北京时间 = UTC+8
        dt_utc = dt_beijing - timedelta(hours=8)
        return dt_utc.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"北京时间转UTC出错: {date_str}, 错误: {e}")
        raise


def convert_to_beijing_time(utc_time):
    if isinstance(utc_time, pd.Timestamp):
        utc_time = utc_time.tz_localize('UTC').tz_convert('Asia/Shanghai')
        return utc_time.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(utc_time, datetime):
        dt = utc_time.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Shanghai'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(utc_time, str):
        try:
            dt = datetime.strptime(utc_time, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            dt = datetime.strptime(utc_time, '%Y-%m-%d %H:%M:%S')
        dt = pytz.utc.localize(dt).astimezone(pytz.timezone('Asia/Shanghai'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return str(utc_time)

def get_closest_records(df, dev_col='device', time_col='data_time'):
    target_minutes = [0,15,30,45]
    df = df.copy()
    df['hour'] = df[time_col].dt.floor('h')
    closest_rows = []
    for hour in df['hour'].unique():
        df_hour = df[df['hour']==hour].copy()
        for m in target_minutes:
            target_time = hour + timedelta(minutes=m)
            if df_hour.empty:
                continue
            df_hour['time_diff'] = (df_hour[time_col]-target_time).abs()
            idx_min = df_hour['time_diff'].idxmin()
            row = df_hour.loc[idx_min].copy()
            row[time_col] = target_time
            closest_rows.append(row)
    if closest_rows:
        return pd.DataFrame(closest_rows).drop(columns=['hour','time_diff'], errors='ignore').sort_values(time_col).reset_index(drop=True)
    else:
        return pd.DataFrame()

def query_and_process(start_date, end_date, devices, clickhouse_config):
    results = []
    start_full = start_date + ' 00:00:00'
    end_full = end_date + ' 23:59:59'

    base_folder = "./results"
    os.makedirs(base_folder, exist_ok=True)

    for device in devices:
        try:
            # 每个设备单独子文件夹
            folder_name = safe_folder_name(f"{device}_raw_data_{start_full}_to_{end_full}")
            device_folder = os.path.join(base_folder, folder_name)
            os.makedirs(device_folder, exist_ok=True)

            client = clickhouse_connect.get_client(**clickhouse_config)

            # --- 查询 HWS ---
            hws_query = f"""
            SELECT data_time, device, Pa, Rc, Ta, Ua
            FROM dwd_hws_data
            WHERE data_time BETWEEN '{beijing_to_utc(start_full)}' AND '{beijing_to_utc(end_full)}'
            AND device='{device}' ORDER BY data_time
            """
            hws_result = client.query(hws_query)
            hws_df = pd.DataFrame(hws_result.result_rows, columns=hws_result.column_names)
            if not hws_df.empty:
                hws_df['data_time'] = pd.to_datetime(hws_df['data_time'].apply(convert_to_beijing_time))
            raw_hws_file = os.path.join(device_folder, f'dwd_hws_data_raw_{device}.csv')
            hws_df.to_csv(raw_hws_file, index=False, quoting=csv.QUOTE_NONNUMERIC)

            # --- 查询 PWV ---
            pwv_query = f"""
            SELECT data_time, device, pwv
            FROM dwd_pwv_data
            WHERE data_time BETWEEN '{beijing_to_utc(start_full)}' AND '{beijing_to_utc(end_full)}'
            AND device='{device}' ORDER BY data_time
            """
            pwv_result = client.query(pwv_query)
            pwv_df = pd.DataFrame(pwv_result.result_rows, columns=pwv_result.column_names)
            if not pwv_df.empty:
                pwv_df['data_time'] = pd.to_datetime(pwv_df['data_time'].apply(convert_to_beijing_time))
            raw_pwv_file = os.path.join(device_folder, f'dwd_pwv_data_raw_{device}.csv')
            pwv_df.to_csv(raw_pwv_file, index=False, quoting=csv.QUOTE_NONNUMERIC)

            # --- 查询预测数据 ---
            pred_query = f"""
            SELECT predict_time, device, real_rainfall_transient, predict_rainfall
            FROM dwd_predict_real_data
            WHERE predict_time BETWEEN '{beijing_to_utc(start_full)}' AND '{beijing_to_utc(end_full)}'
            AND device='{device}' ORDER BY predict_time
            """
            pred_result = client.query(pred_query)
            pred_df = pd.DataFrame(pred_result.result_rows, columns=pred_result.column_names)
            if not pred_df.empty:
                pred_df['predict_time'] = pd.to_datetime(pred_df['predict_time'].apply(convert_to_beijing_time))
            raw_pred_file = os.path.join(device_folder, f'dwd_predict_real_data_raw_{device}.csv')
            pred_df.to_csv(raw_pred_file, index=False, quoting=csv.QUOTE_NONNUMERIC)

            # --- 取最接近 00/15/30/45 分钟 ---
            hws_closest = get_closest_records(hws_df)
            pwv_closest = get_closest_records(pwv_df, time_col='data_time')

            # --- 合并 HWS + PWV ---
            merged_df = pd.merge(
                hws_closest,
                pwv_closest[['data_time','pwv']],
                on='data_time',
                how='inner'
            )
            merged_df = merged_df.rename(columns={'data_time':'date','Pa':'sp','Rc':'tp','Ta':'t2m','Ua':'rh'})

            # --- 合并预测 ---
            pred_df = pred_df.rename(columns={'predict_time':'date'})
            merged_df['date'] = pd.to_datetime(merged_df['date'])
            merged_df = pd.merge(
                merged_df,
                pred_df[['date','real_rainfall_transient']],
                on='date',
                how='left'
            )
            merged_df['tp'] = merged_df['real_rainfall_transient'].fillna(0)
            merged_df.drop(columns=['real_rainfall_transient'], inplace=True)

            final_cols = ['date','t2m','sp','rh','pwv','tp']
            merged_df = merged_df[final_cols]

            output_file = os.path.join(device_folder, f'dwd_hws_data_{device}_result.csv')
            merged_df.to_csv(output_file, index=False, quoting=csv.QUOTE_NONNUMERIC)

            results.append({
                "device": device,
                "folder": device_folder,
                "files": [raw_hws_file, raw_pwv_file, raw_pred_file, output_file]
            })
        except Exception as e:
            results.append({"device": device, "error": str(e)})

    return results



from flask import request, jsonify

@app.route("/api/query-devices", methods=["POST"])
def api_query_devices():
    try:
        data = request.get_json(force=True)
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        devices = data.get("devices", [])
        clickhouse_cfg = data.get("clickhouse_config")

        if not clickhouse_cfg:
            return jsonify({"ok": False, "error": "缺少 ClickHouse 配置"})

        results = query_and_process(start_date, end_date, devices, clickhouse_cfg)
        return jsonify({"ok": True, "results": results})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)})



# ---------------------------
# Module 2: 荆楚水库数据合并
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

# 常量定义
land_vars = ['2m_temperature', '2m_dewpoint_temperature', 'surface_pressure', 'total_precipitation']
pressure_vars = ['specific_humidity']
pressure_levels = ['1000', '925', '850', '700', '500', '300']
g = 9.80665  # 重力加速度


def download_era5_controlled(area_name, year, month, bbox, output_nc_dir, delay=2):
    """
    下载 ERA5-Land 和 ERA5-Pressure 数据（自动跳过已存在的文件）
    """
    area_dir = os.path.join(output_nc_dir, area_name)
    os.makedirs(area_dir, exist_ok=True)

    days_in_month = calendar.monthrange(year, month)[1]
    day_list = [f"{d:02d}" for d in range(1, days_in_month + 1)]

    # === ERA5-Land ===
    fn_land = os.path.join(area_dir, f"era5_land_{year}_{month:02d}.nc")
    if not os.path.exists(fn_land):
        cdsapi.Client().retrieve("reanalysis-era5-land", {
            "variable": land_vars,
            "year": str(year),
            "month": f"{month:02d}",
            "day": day_list,
            "time": [f"{h:02d}:00" for h in range(24)],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": bbox
        }, fn_land)
        print(f"[{area_name}] ERA5-Land 下载完成: {fn_land}")
        time.sleep(delay)
    else:
        print(f"[{area_name}] 文件已存在: {fn_land}")

    # === ERA5-Pressure ===
    fn_press = os.path.join(area_dir, f"era5_press_{year}_{month:02d}.nc")
    if not os.path.exists(fn_press):
        cdsapi.Client().retrieve("reanalysis-era5-pressure-levels", {
            "product_type": "reanalysis",
            "variable": pressure_vars,
            "pressure_level": pressure_levels,
            "year": str(year),
            "month": f"{month:02d}",
            "day": day_list,
            "time": [f"{h:02d}:00" for h in range(24)],
            "data_format": "netcdf",
            "download_format": "unarchived",
            "area": bbox
        }, fn_press)
        print(f"[{area_name}] ERA5-Pressure 下载完成: {fn_press}")
        time.sleep(delay)
    else:
        print(f"[{area_name}] 文件已存在: {fn_press}")

    return fn_land, fn_press


def process_and_save_csv(device_name, lat, lon, nc_files, area_name, output_dir):
    """
    读取 ERA5 Land + Pressure 数据，计算 PWV、RH 等并保存为 CSV。
    """
    os.makedirs(output_dir, exist_ok=True)
    buffer = []

    for fn_land, fn_press in nc_files:
        with xr.open_dataset(fn_land) as ds_land, xr.open_dataset(fn_press) as ds_press:
            time_coord = 'valid_time'
            times = ds_land[time_coord].values

            # ---- PWV 计算 ----
            q = ds_press['q'].sel(latitude=lat, longitude=lon, method='nearest')
            p_levels = ds_press['pressure_level'].values * 100  # Pa
            sort_idx = np.argsort(-p_levels)
            p_sorted = p_levels[sort_idx]

            pwv_list = []
            for t_idx, t_val in enumerate(times):
                q_t = q.isel({time_coord: t_idx}).values
                q_sorted = q_t[sort_idx]
                dp = p_sorted[:-1] - p_sorted[1:]
                pwv = np.sum((q_sorted[:-1] + q_sorted[1:]) / 2 * dp) / g
                pwv_list.append(pwv)

            # ---- Land 变量 ----
            t2m_vals = ds_land['t2m'].sel(latitude=lat, longitude=lon, method='nearest').values
            d2m_vals = ds_land['d2m'].sel(latitude=lat, longitude=lon, method='nearest').values
            sp_vals  = ds_land['sp'].sel(latitude=lat, longitude=lon, method='nearest').values
            tp_vals  = ds_land['tp'].sel(latitude=lat, longitude=lon, method='nearest').values  # 累计降水 (m)

            tp_series = pd.Series(tp_vals, index=times)
            tp_diff = tp_series.diff().fillna(0).clip(lower=0) * 1000  # mm

            # ---- 转为 15 分钟时间间隔 ----
            for t_idx, t_val in enumerate(times):
                tp_hour_mm = float(tp_diff.iloc[t_idx])
                t2m_val = float(t2m_vals[t_idx])
                d2m_val = float(d2m_vals[t_idx])
                sp_val = float(sp_vals[t_idx])
                pwv_val = float(pwv_list[t_idx])

                t2m_c = t2m_val - 273.15
                dew_c = d2m_val - 273.15
                rh = float(np.exp((17.269 * dew_c) / (237.3 + dew_c) -
                                  (17.269 * t2m_c) / (237.3 + t2m_c)) * 100)
                rh = min(max(rh, 0), 100)

                tp_15min = tp_hour_mm / 4
                for i in range(4):
                    dt = pd.to_datetime(str(t_val)) - pd.Timedelta(hours=1) + pd.Timedelta(minutes=15 * (i + 1))
                    buffer.append({
                        'date': dt,
                        't2m': t2m_c,
                        'sp': sp_val / 100,  # hPa
                        'rh': rh,
                        'pwv': pwv_val,
                        'tp': tp_15min
                    })

    df = pd.DataFrame(buffer)
    for col in ['t2m', 'sp', 'rh', 'pwv', 'tp']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    csv_file = os.path.join(output_dir, f"{device_name}_pressure_land.csv")
    df.to_csv(csv_file, index=False)
    print(f"[完成] 设备 {device_name} 数据保存到: {csv_file}")
    return csv_file


def era5_download_and_process(device, start_year, start_month, end_year, end_month, target_lat, target_lon, area):
    """
    主函数：下载 Land + Pressure 数据并合并处理成 CSV。
    """
    output_nc_dir = os.path.join(app.config['RESULT_FOLDER'], "nc", f"{device}")
    output_csv_dir = os.path.join(app.config['RESULT_FOLDER'], "六要素数据")
    ensure_dir(output_nc_dir)
    ensure_dir(output_csv_dir)

    area_name = f"area_{device}"
    nc_files_all = []

    for year in range(start_year, end_year + 1):
        start_m = start_month if year == start_year else 1
        end_m = end_month if year == end_year else 12
        for month in range(start_m, end_m + 1):
            nc_pair = download_era5_controlled(area_name, year, month, area, output_nc_dir, delay=2)
            nc_files_all.append(nc_pair)

    csv_file = process_and_save_csv(device, target_lat, target_lon, nc_files_all, area_name, output_csv_dir)
    return csv_file


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

def merge_months(folders, output_folder):
    """
    folders: 列表，包含用户填写的文件夹路径
    output_folder: 输出文件夹
    """
    ensure_dir(output_folder)

    # 收集每个文件夹的文件列表
    files_list = []
    for folder in folders:
        if os.path.isdir(folder):
            files_list.append(set(os.listdir(folder)))
        else:
            files_list.append(set())

    # 所有文件取并集
    all_files = set().union(*files_list)
    logs = [f"找到 {len(all_files)} 个文件"]
    outputs = []

    for filename in all_files:
        dfs = []
        for i, folder in enumerate(folders):
            if filename in files_list[i]:
                dfs.append(pd.read_csv(os.path.join(folder, filename), sep=","))

        if not dfs:
            continue

        # 删除全为空的列
        dfs = [df.dropna(axis=1, how='all') for df in dfs if not df.empty]
        if dfs:
            df_all = pd.concat(dfs, ignore_index=True)
        else:
            df_all = pd.DataFrame()

        if "date" in df_all.columns:
            try:
                # 修改这里：处理两种日期格式
                df_all["date"] = pd.to_datetime(
                    df_all["date"], 
                    format='mixed',  # 自动处理混合格式
                    errors='coerce'  # 转换失败设为NaT
                )
                
                # 删除转换失败的日期行
                original_count = len(df_all)
                df_all = df_all.dropna(subset=["date"])
                if len(df_all) < original_count:
                    logs.append(f"文件 {filename}: 删除了 {original_count - len(df_all)} 行无效日期数据")
                
                # 按日期排序并去重
                df_all = df_all.sort_values(by="date").reset_index(drop=True)
                df_all = df_all.drop_duplicates(subset="date", keep="first")
                
            except Exception as e:
                logs.append(f"文件 {filename} 日期处理失败: {str(e)}")
                # 继续处理，但不进行日期相关的操作

        try:
            out_path = os.path.join(output_folder, filename)
            df_all.to_csv(out_path, index=False, encoding="utf-8")
            outputs.append(out_path)
            logs.append(f"成功合并文件: {filename}")
        except Exception as e:
            logs.append(f"保存文件 {filename} 失败: {str(e)}")

    return logs, outputs


@app.route("/api/merge-months", methods=["POST"])
def api_merge_months():
    data = request.get_json(force=True)
    folder_5_6 = data.get("folder_5_6", "").strip()
    folder_7 = data.get("folder_7", "").strip()
    folder_8 = data.get("folder_8", "").strip()
    output_folder = data.get("output_folder", "").strip()

    # 输出文件夹必须填写
    if not output_folder:
        return json_err("输出文件夹路径不能为空")

    # 收集非空输入文件夹
    folders = [f for f in [folder_5_6, folder_7, folder_8] if f]

    # 至少填写两个文件夹
    if len(folders) < 2:
        return json_err("请至少填写两个需要合并的文件夹路径")

    # 转换为绝对路径
    folders = [os.path.abspath(f) for f in folders]
    output_folder = os.path.abspath(output_folder)
    ensure_dir(output_folder)

    try:
        logs, outputs = merge_months(folders, output_folder)
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