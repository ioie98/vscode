# #本地测试版
# import pymysql
# from clickhouse_connect import get_client
# from datetime import datetime, timedelta
#
# # ------------------ 配置 ------------------
# BH_SRC_CONFIG = {
#     "host": "bytehouse.huoshan.accurain.cn",
#     "port": 80,
#     "username": "accurain_guest",
#     "password": "V3VuWS7%FWs@u",
#     "database": "accurain",
#     "secure": False
# }
#
# BH_DST_CONFIG = {
#     "host": "bytehouse.huoshan.accurain.cn",
#     "port": 80,
#     "username": "accuraindev",
#     "password": "2P%#9N8qVSb@sQ",
#     "database": "dev",
#     "secure": False
# }
#
# MYSQL_CONFIG = {
#     "host": "115.190.81.184",
#     "port": 30730,
#     "user": "gnss",
#     "password": "klv!dopY$uN8I",
#     "database": "gnss"
# }
#
# # ------------------ 工具函数 ------------------
# def get_mysql_devices():
#     conn = pymysql.connect(**MYSQL_CONFIG)
#     devices = []
#     with conn.cursor() as cursor:
#         cursor.execute("SELECT ID FROM sb_jbxx")
#         rows = cursor.fetchall()
#         devices = [row[0] for row in rows]
#     conn.close()
#     return devices
#
# def get_device_location(device):
#     conn = pymysql.connect(**MYSQL_CONFIG)
#     with conn.cursor() as cursor:
#         cursor.execute("SELECT LNG, LAT FROM sb_jbxx WHERE ID=%s", (device,))
#         row = cursor.fetchone()
#     conn.close()
#     if row:
#         return row[0], row[1]
#     else:
#         return None, None
#
# def nearest_15min(ts):
#     """返回最接近的 00/15/30/45 分钟刻度（UTC）"""
#     minute = (ts.minute // 15) * 15
#     lower = ts.replace(minute=minute, second=0, microsecond=0)
#     upper = lower + timedelta(minutes=15)
#     if abs(ts - lower) <= abs(ts - upper):
#         return lower
#     else:
#         return upper
#
# # ------------------ 数据同步（带start_time） ------------------
# def process_pwv(client_src, device, start_time=None):
#     query = f"""
#         SELECT data_time, device, pwv
#         FROM dwd_pwv_data
#         WHERE device = '{device}'
#     """
#     if start_time:
#         query += f" AND data_time >= toDateTime('{start_time.strftime('%Y-%m-%d %H:%M:%S')}')"
#
#     data = client_src.query(query).result_rows
#
#     filtered = {}
#     for dt_val, dev, pwv in data:
#         ts = dt_val
#         key = nearest_15min(ts)
#         if key not in filtered or abs(ts - key) < abs(filtered[key][0] - key):
#             filtered[key] = (ts, pwv)
#
#     insert_data = []
#     for key, (ts, pwv) in filtered.items():
#         lon, lat = get_device_location(device)
#         insert_data.append({
#             "data_time": key,
#             "device": device,
#             "lon": lon,
#             "lau": lat,
#             "pwv": pwv,
#             "datatype": "Device"
#         })
#
#     if insert_data:
#         print(f"[PWV] Device {device} 准备插入 {len(insert_data)} 条数据:")
#         for d in insert_data:
#             print(d)
#
# def process_hws(client_src, device, start_time=None):
#     query = f"""
#         SELECT data_time, device, Pa, Ta, Ua
#         FROM dwd_hws_data
#         WHERE device = '{device}'
#     """
#     if start_time:
#         query += f" AND data_time >= toDateTime('{start_time.strftime('%Y-%m-%d %H:%M:%S')}')"
#
#     data = client_src.query(query).result_rows
#
#     filtered = {}
#     for dt_val, dev, Pa, Ta, Ua in data:
#         ts = dt_val
#         key = nearest_15min(ts)
#         if key not in filtered or abs(ts - key) < abs(filtered[key][0] - key):
#             filtered[key] = (ts, Pa, Ta, Ua)
#
#     insert_data = []
#     for key, (ts, Pa, Ta, Ua) in filtered.items():
#         insert_data.append({
#             "data_time": key,
#             "device": device,
#             "ta": Ta,
#             "pa": Pa,
#             "ua": Ua,
#             "data_type": "Device"
#         })
#
#     if insert_data:
#         print(f"[HWS] Device {device} 准备插入 {len(insert_data)} 条数据:")
#         for d in insert_data:
#             print(d)
#
# def process_raingauge(client_src, device, start_time=None):
#     query = f"""
#         SELECT data_time, device, rainfall
#         FROM dwd_raingauge_15min_data
#         WHERE device = '{device}' AND data_type = 1
#     """
#     if start_time:
#         query += f" AND data_time >= toDateTime('{start_time.strftime('%Y-%m-%d %H:%M:%S')}')"
#
#     data = client_src.query(query).result_rows
#
#     filtered = {}
#     for dt_val, dev, rainfall in data:
#         ts = dt_val
#         key = nearest_15min(ts)
#         if key not in filtered or abs(ts - key) < abs(filtered[key][0] - key):
#             filtered[key] = (ts, rainfall)
#
#     insert_data = []
#     for key, (ts, rainfall) in filtered.items():
#         insert_data.append({
#             "data_time": key,
#             "device": device,
#             "rainfall": rainfall,
#             "data_type": "Device",
#             "rain_time": 15,
#             "reset": 0
#         })
#
#     if insert_data:
#         print(f"[RAINGAUGE] Device {device} 准备插入 {len(insert_data)} 条数据:")
#         for d in insert_data:
#             print(d)
#
# # ------------------ 主函数 ------------------
# def main(devices, start_time=None):
#     client_src = get_client(**BH_SRC_CONFIG)
#     client_dst = get_client(**BH_DST_CONFIG)  # 调试打印，不插入，但保留结构
#
#     print("同步设备列表:", devices)
#     if start_time:
#         print("同步 start_time:", start_time)
#
#     for device in devices:
#         process_pwv(client_src, device, start_time=start_time)
#         process_hws(client_src, device, start_time=start_time)
#         process_raingauge(client_src, device, start_time=start_time)
#
#     print("数据同步调试完成！")
#
# # ------------------ 执行 ------------------
# if __name__ == "__main__":
#     devices_env = "b100"  # 或 "MYSQL" / "b100,b72,b101"
#
#     if devices_env.upper() == "MYSQL":
#         DEVICES = get_mysql_devices()
#     else:
#         DEVICES = [d.strip() for d in devices_env.split(",") if d.strip()]
#
#     START_TIME = datetime(2025, 12, 12, 12, 0, 0)  # 指定开始时间（UTC）
#
#     main(DEVICES, start_time=START_TIME)
# #





import pymysql
import traceback
import pandas as pd
from clickhouse_connect import get_client
from datetime import datetime, timedelta

# ------------------ 配置 ------------------
BH_SRC_CONFIG = {
    "host": "bytehouse.huoshan.accurain.cn",
    "port": 80,
    "username": "accurain_guest",
    "password": "V3VuWS7%FWs@u",
    "database": "accurain",
    "secure": False
}

BH_DST_CONFIG = {
    "host": "bytehouse.huoshan.accurain.cn",
    "port": 80,
    "username": "accuraindev",
    "password": "2P%#9N8qVSb@sQ",
    "database": "dev",
    "secure": False,
    "compression":'gzip',
}

MYSQL_CONFIG = {
    "host": "115.190.81.184",
    "port": 30730,
    "user": "gnss",
    "password": "klv!dopY$uN8I",
    "database": "gnss"
}

TABLES = {
    "pwv": {
        "table": "ods_pwv_external",
        "fields": ["data_time", "device", "lon", "lau", "pwv", "data_type"]
    },
    "hws": {
        "table": "ods_hws_external",
        "fields": ["data_time", "device", "ta", "pa", "ua", "data_type"]
    },
    "rain": {
        "table": "ods_raingauge_external",
        "fields": ["data_time", "device", "rainfall", "data_type", "rain_time", "reset"]
    }
}

# ------------------ 工具函数 ------------------
def get_mysql_devices():
    conn = pymysql.connect(**MYSQL_CONFIG)
    devices = []
    with conn.cursor() as cursor:
        cursor.execute("SELECT ID FROM sb_jbxx")
        devices = [row[0] for row in cursor.fetchall()]
    conn.close()
    return devices

def get_device_location(device):
    conn = pymysql.connect(**MYSQL_CONFIG)
    with conn.cursor() as cursor:
        cursor.execute("SELECT LNG, LAT FROM sb_jbxx WHERE ID=%s", (device,))
        row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None

def nearest_15min(ts):
    minute = (ts.minute // 15) * 15
    lower = ts.replace(minute=minute, second=0, microsecond=0)
    upper = lower + timedelta(minutes=15)
    return lower if abs(ts - lower) <= abs(ts - upper) else upper

def to_float(x):
    try:
        return float(str(x).strip()) if x is not None and str(x).strip() != '' else None
    except:
        return None

def to_int16(x):
    try:
        return int(float(str(x).strip())) if x is not None and str(x).strip() != '' else None
    except:
        return None

def to_int8(x):
    try:
        return int(float(str(x).strip())) if x is not None and str(x).strip() != '' else None
    except:
        return None

# ------------------ 安全插入函数 ------------------
def safe_insert(client_dst, table_name, records, columns, debug_name):
    if not records:
        print(f"[{debug_name}] 没有数据，跳过插入")
        return 0

    df = pd.DataFrame(records)
    df = df[columns]  # 强制列顺序

    # 处理 data_time 列，保证是 datetime64[ns, UTC]
    if 'data_time' in df.columns:
        df['data_time'] = pd.to_datetime(df['data_time'], utc=True, errors='coerce')

    # 数值列强制转 float，避免 KeyError
    for col in df.columns:
        if col not in ["device", "data_type", "data_time"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    try:
        client_dst.insert(table_name, df, column_names=columns)
        print(f"[{debug_name}] 插入数量: {len(df)}")
        return len(df)
    except Exception as e:
        print(f"[{debug_name}] 插入失败: {e}")
        traceback.print_exc()
        return 0


# ------------------ 批量处理 ------------------
def batch_process(client_src, client_dst, device, start_time=None):
    inserted_counts = {"pwv": 0, "hws": 0, "rain": 0}

    # ----------------- PWV -----------------
    try:
        query = f"SELECT data_time, device, pwv FROM dwd_pwv_data WHERE device='{device}'"
        if start_time:
            query += f" AND data_time >= toDateTime('{start_time:%Y-%m-%d %H:%M:%S}')"
        data = client_src.query(query).result_rows

        filtered = {}
        for dt_val, dev, pwv in data:
            key = nearest_15min(dt_val)
            if key not in filtered or abs(dt_val - key) < abs(filtered[key][0] - key):
                filtered[key] = (dt_val, pwv)

        lon, lat = get_device_location(device)
        records = []
        for key, (dt_val, pwv_val) in filtered.items():
            if lon is None and lat is None and pwv_val is None:
                continue
            record = {
                "data_time": pd.to_datetime(key, utc=True),  # 强制 UTC
                "device": device,
                "lon": float(lon) if lon is not None else None,
                "lau": float(lat) if lat is not None else None,
                "pwv": float(pwv_val) if pwv_val is not None else None,
                "data_type": "Device"
            }
            records.append(record)
            # print("[DEBUG PWV] 准备插入的数据:")
            # print(record)

        inserted_counts["pwv"] = safe_insert(client_dst, "ods_pwv_external", records, TABLES['pwv']['fields'], "PWV")
    except Exception as e:
        print(f"[PWV] 处理失败: {e}")
        traceback.print_exc()

    # ----------------- HWS -----------------
    try:
        query = f"SELECT data_time, device, Pa, Ta, Ua FROM dwd_hws_data WHERE device='{device}'"
        if start_time:
            query += f" AND data_time >= toDateTime('{start_time:%Y-%m-%d %H:%M:%S}')"
        data = client_src.query(query).result_rows

        filtered = {}
        for dt_val, dev, Pa, Ta, Ua in data:
            key = nearest_15min(dt_val)
            if key not in filtered or abs(dt_val - key) < abs(filtered[key][0] - key):
                filtered[key] = (dt_val, Pa, Ta, Ua)

        records = []
        for key, (dt_val, Pa, Ta, Ua) in filtered.items():
            record = {
                "data_time": pd.to_datetime(key, utc=True),  # 强制 UTC
                "device": device,
                "ta": float(Ta) if Ta is not None else None,
                "pa": float(Pa) if Pa is not None else None,
                "ua": float(Ua) if Ua is not None else None,
                "data_type": "Device"
            }
            records.append(record)
            # print("[DEBUG HWS] 准备插入的数据:")
            # print(record)

        inserted_counts["hws"] = safe_insert(client_dst, "ods_hws_external", records, TABLES['hws']['fields'], "HWS")
    except Exception as e:
        print(f"[HWS] 处理失败: {e}")
        traceback.print_exc()

    # ----------------- Rain -----------------
    try:
        query = f"SELECT data_time, device, rainfall FROM dwd_raingauge_15min_data WHERE device='{device}' AND data_type=1"
        if start_time:
            query += f" AND data_time >= toDateTime('{start_time:%Y-%m-%d %H:%M:%S}')"
        data = client_src.query(query).result_rows

        filtered = {}
        for dt_val, dev, rainfall in data:
            key = nearest_15min(dt_val)
            if key not in filtered or abs(dt_val - key) < abs(filtered[key][0] - key):
                filtered[key] = (dt_val, rainfall)

        records = []
        for key, (dt_val, rainfall) in filtered.items():
            record = {
                "data_time": pd.to_datetime(key, utc=True),  # 强制 UTC
                "device": device,
                "rainfall": float(rainfall) if rainfall is not None else 0.0,
                "data_type": "Device",
                "rain_time": 15,
                "reset": 0
            }
            records.append(record)
            # print("[DEBUG RAIN] 准备插入的数据:")
            # print(record)

        inserted_counts["rain"] = safe_insert(client_dst, "ods_raingauge_external", records, TABLES['rain']['fields'], "RAINGAUGE")
    except Exception as e:
        print(f"[RAIN] 处理失败: {e}")
        traceback.print_exc()

    return inserted_counts



# ------------------ 主函数 ------------------
def main(devices, start_time=None):
    client_src = get_client(**BH_SRC_CONFIG)
    client_dst = get_client(**BH_DST_CONFIG)

    print("同步设备列表:", devices)
    if start_time:
        print("同步 start_time:", start_time)

    for device in devices:
        counts = batch_process(client_src, client_dst, device, start_time=start_time)
        print(f"[{device}] 插入数量: {counts}")

    print("数据同步完成！")

# ------------------ 执行 ------------------
if __name__ == "__main__":
    # devices_env = "b100"  # 或 "MYSQL" / "b100,b72,b101"
    devices_env = "MYSQL"  # 或 "MYSQL" / "b100,b72,b101"

    if devices_env.upper() == "MYSQL":
        DEVICES = get_mysql_devices()
    else:
        DEVICES = [d.strip() for d in devices_env.split(",") if d.strip()]

    START_TIME = datetime(2024, 12, 1, 1, 0, 0)
    main(DEVICES, start_time=START_TIME)

