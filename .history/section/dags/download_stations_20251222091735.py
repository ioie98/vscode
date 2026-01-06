import tos  # 确保已安装：pip install tos
from tqdm.asyncio import tqdm as atqdm
import pandas as pd
import os 
import time
import aiohttp
import asyncio
import random
from datetime import datetime, timedelta, timezone
import numpy as np 

# ------------------ 配置信息 ------------------
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
STATION_INFO_FP = os.path.join(STATIC_DIR, "station_info_new.csv")
TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
OBS_DATA_URL_PATTERN = "http://www.nmc.cn/rest/weather?stationid={code}"

# 并发控制参数
MAX_CONCURRENT = 30  
TIMEOUT = 8  
MAX_RETRIES = 3  
RETRY_DELAY_BASE = 0.5  

# 时间过滤参数
HOURS_BACK = 24  

# ------------------ TOS 客户端配置 ------------------
ENDPOINT = "tos-cn-beijing.volces.com"
REGION = "cn-beijing"
BUCKET_NAME = "gnss"
AK = os.getenv('TOS_ACCESS_KEY')
SK = os.getenv('TOS_SECRET_KEY')

AK =
SK =

def get_tos_client():
    if not AK or not SK:
        print("错误: 环境变量 TOS_ACCESS_KEY 或 TOS_SECRET_KEY 未设置！")
        return None
    return tos.TosClientV2(AK, SK, ENDPOINT, REGION)

def get_station_info():
    if not os.path.exists(STATION_INFO_FP):
        raise FileNotFoundError(f"未找到站点信息文件: {STATION_INFO_FP}")
    return pd.read_csv(STATION_INFO_FP)

async def fetch_station_data(session, code, sid, lon, lat, semaphore, time_threshold=None):
    """异步获取单个站点的观测数据"""
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    delay = RETRY_DELAY_BASE * (2 ** attempt) + random.uniform(0, 0.5)
                    await asyncio.sleep(delay)
                
                URL = OBS_DATA_URL_PATTERN.format(code=code) + f"&_={int(time.time()*1000)}"
                async with session.get(URL, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and "data" in data and data["data"]:
                            records = []
                            for passedchart in data["data"].get("passedchart", []):
                                try:
                                    timestr = passedchart["time"]
                                    dt = (
                                        datetime.fromisoformat(timestr)
                                        .replace(tzinfo=timezone(timedelta(hours=8)))
                                        .astimezone(timezone.utc)
                                    )
                                    if time_threshold is not None and dt < time_threshold:
                                        continue
                                    
                                    records.append({
                                        "sid": sid, "lon": lon, "lat": lat, "datetime": dt,
                                        "wind_speed": passedchart["windSpeed"],
                                        "wind_direction": passedchart["windDirection"],
                                        "temperature": passedchart["temperature"],
                                        "humidity": passedchart["humidity"],
                                        "pressure": passedchart["pressure"],
                                        "rain1h": passedchart["rain1h"],
                                    })
                                except (KeyError, TypeError, ValueError):
                                    continue
                            return {"code": code, "records": records, "error": None, "retries": attempt}
                        else:
                            return {"code": code, "records": [], "error": "no_data", "retries": attempt}
                    elif resp.status == 429:
                        if attempt < MAX_RETRIES - 1: continue
                        return {"code": code, "records": [], "error": f"http_{resp.status}", "retries": attempt}
                    else:
                        return {"code": code, "records": [], "error": f"http_{resp.status}", "retries": attempt}
            except Exception as e:
                if attempt < MAX_RETRIES - 1: continue
                return {"code": code, "records": [], "error": f"exception_{str(e)[:50]}", "retries": attempt}
        return {"code": code, "records": [], "error": "max_retries_exceeded", "retries": MAX_RETRIES}

async def prepare_observation_async():
    station_df = get_station_info()
    stations = [
        {"code": str(row["code"]), "sid": row["sid"], "lon": np.round(row["lon"], 3), "lat": np.round(row["lat"], 3)}
        for _, row in station_df.iterrows()
    ]
    
    # --- 时间与路径处理 ---
    now_time = datetime.now()
    year = now_time.strftime("%Y")
    month = now_time.strftime("%m")
    init_time_str = now_time.strftime("%Y%m%d%H")
    
    filename = f"{init_time_str}.csv"
    local_path = os.path.join(TMP_DIR, filename)
    tos_key = f"stations/data/{year}/{month}/{filename}"
    
    # 时间过滤阈值
    time_threshold = None
    if HOURS_BACK is not None:
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_station_data(session, s["code"], s["sid"], s["lon"], s["lat"], semaphore, time_threshold) 
                 for s in stations]
        results = []
        for coro in atqdm.as_completed(tasks, total=len(tasks), desc="下载进度"):
            results.append(await coro)
    
    records = []
    for result in results:
        if not result["error"]:
            records.extend(result["records"])
    
    if records:
        # 1. 保存到本地
        df = pd.DataFrame(records)
        df.to_csv(local_path, index=False)
        print(f"\n本地保存成功: {local_path}")
        
        # 2. 上传到 TOS
        client = get_tos_client()
        if client:
            try:
                print(f"正在上传至 TOS: {tos_key} ...")
                client.put_object_from_file(BUCKET_NAME, tos_key, local_path)
                print(f"--- 上传成功！Bucket: {BUCKET_NAME} ---")
            except Exception as e:
                print(f"--- TOS 上传失败: {e} ---")
    else:
        print("警告: 未抓取到有效观测数据。")

def prepare_all():
    os.makedirs(TMP_DIR, exist_ok=True)
    asyncio.run(prepare_observation_async())

if __name__ == "__main__":
    prepare_all()