from tqdm.asyncio import tqdm as atqdm
import pandas as pd
import os 
import time
import aiohttp
import asyncio
import random
from datetime import datetime, timedelta, timezone
import numpy as np 

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
STATION_INFO_FP = os.path.join(STATIC_DIR, "station_info_new.csv")
TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
OBS_DATA_URL_PATTERN = "http://www.nmc.cn/rest/weather?stationid={code}"

# 并发控制参数
MAX_CONCURRENT = 30  # 最大并发数，降低以避免触发限流
TIMEOUT = 8  # 请求超时时间（秒），适当增加
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY_BASE = 0.5  # 重试延迟基数（秒）

# 时间过滤参数
HOURS_BACK = 24  # 只下载最近N小时的数据，设为None则不限制 # 最多24小时


def get_station_info():
    df = pd.read_csv(STATION_INFO_FP)
    return df


async def fetch_station_data(session, code, sid, lon, lat, semaphore, time_threshold=None):
    """
    异步获取单个站点的观测数据，带重试机制
    
    Args:
        time_threshold: 时间阈值（UTC时间），只保留此时间之后的数据，None表示不过滤
    """
    async with semaphore:  # 控制并发数
        for attempt in range(MAX_RETRIES):
            try:
                # 添加随机延迟，避免请求过于集中
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
                                    wind_speed = passedchart["windSpeed"]
                                    wind_direction = passedchart["windDirection"]
                                    temperature = passedchart["temperature"]
                                    humidity = passedchart["humidity"]
                                    pressure = passedchart["pressure"]
                                    rain1h = passedchart["rain1h"]
                                    timestr = passedchart["time"]
                                    dt = (
                                        datetime.fromisoformat(timestr)
                                        .replace(tzinfo=timezone(timedelta(hours=8)))
                                        .astimezone(timezone.utc)
                                    )
                                    
                                    # 时间过滤：只保留时间阈值之后的数据
                                    if time_threshold is not None and dt < time_threshold:
                                        continue
                                    
                                    parsed_data = {
                                        "sid": sid,
                                        "lon": lon,
                                        "lat": lat,
                                        "datetime": dt,
                                        "wind_speed": wind_speed,
                                        "wind_direction": wind_direction,
                                        "temperature": temperature,
                                        "humidity": humidity,
                                        "pressure": pressure,
                                        "rain1h": rain1h,
                                    }
                                    records.append(parsed_data)
                                except (KeyError, TypeError, ValueError) as e:
                                    continue
                            
                            return {"code": code, "records": records, "error": None, "retries": attempt}
                        else:
                            # 无数据，不重试
                            return {"code": code, "records": [], "error": "no_data", "retries": attempt}
                    elif resp.status == 429:  # 限流，需要重试
                        if attempt < MAX_RETRIES - 1:
                            continue
                        return {"code": code, "records": [], "error": f"http_{resp.status}", "retries": attempt}
                    else:
                        # 其他HTTP错误，不重试
                        return {"code": code, "records": [], "error": f"http_{resp.status}", "retries": attempt}
            except asyncio.TimeoutError:
                if attempt < MAX_RETRIES - 1:
                    continue  # 超时重试
                return {"code": code, "records": [], "error": "timeout", "retries": attempt}
            except aiohttp.ClientError:
                if attempt < MAX_RETRIES - 1:
                    continue  # 网络错误重试
                return {"code": code, "records": [], "error": "client_error", "retries": attempt}
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    continue  # 其他异常重试
                return {"code": code, "records": [], "error": f"exception_{str(e)[:50]}", "retries": attempt}
        
        # 所有重试都失败
        return {"code": code, "records": [], "error": "max_retries_exceeded", "retries": MAX_RETRIES}


async def prepare_observation_async():
    """
    异步并发下载所有站点的观测数据
    """
    station_df = get_station_info()

    url_error_list = []
    data_error_list = []
    codes = station_df["code"].tolist()
    sids = station_df["sid"].tolist()
    lons = station_df["lon"].tolist()
    lats = station_df['lat'].tolist()
    
    # 准备站点信息列表
    stations = [
        {
            "code": code,
            "sid": sids[i],
            "lon": np.round(lons[i], 3),
            "lat": np.round(lats[i], 3)
        }
        for i, code in enumerate(codes)
    ]
    
    print(f"开始下载观测数据，共 {len(stations)} 个站点...")
    print(f"并发数: {MAX_CONCURRENT}, 超时时间: {TIMEOUT}秒, 最大重试次数: {MAX_RETRIES}")
    
    now_time = datetime.now()
    # Initime = datetime.strftime(now_time, "%Y%m%d%H")[:8] + "00"
    Initime = datetime.strftime(now_time, "%Y%m%d%H")
    
    # 计算时间阈值（UTC时间）
    time_threshold = None
    if HOURS_BACK is not None:
        now_utc = datetime.now(timezone.utc)
        time_threshold = now_utc - timedelta(hours=HOURS_BACK)
        print(f"时间过滤: 只下载最近 {HOURS_BACK} 小时的数据（UTC时间 >= {time_threshold.strftime('%Y-%m-%d %H:%M:%S')}）")
    else:
        print("时间过滤: 无限制，下载所有可用数据")
    
    # 创建信号量控制并发数
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    # 创建HTTP会话
    async with aiohttp.ClientSession() as session:
        # 创建所有任务
        tasks = [
            fetch_station_data(session, station["code"], station["sid"], 
                             station["lon"], station["lat"], semaphore, time_threshold)
            for station in stations
        ]
        
        # 并发执行所有任务，显示进度条
        results = []
        for coro in atqdm.as_completed(tasks, total=len(tasks), desc="下载进度"):
            result = await coro
            results.append(result)
    
    # 处理结果
    records = []
    retry_stats = {"total_retries": 0, "retried_stations": 0}
    for result in results:
        if result.get("retries", 0) > 0:
            retry_stats["total_retries"] += result["retries"]
            retry_stats["retried_stations"] += 1
        
        if result["error"]:
            if result["error"].startswith("http_") or result["error"] in ["timeout", "client_error", "max_retries_exceeded"]:
                url_error_list.append(result["code"])
            else:
                data_error_list.append(result["code"])
        else:
            records.extend(result["records"])
    
    # 保存数据
    if records:
        df = pd.DataFrame(records)
        df.to_csv(os.path.join(TMP_DIR, f"{Initime}.csv"), index=False)
        print(
            f"\n观测数据下载完成！"
            f"\n成功下载: {len(df)} 条观测记录"
            f"\n成功站点: {len(set(df['sid'].tolist()))} 个"
            f"\nURL错误: {len(url_error_list)} 个站点"
            f"\n数据错误: {len(data_error_list)} 个站点"
        )
        
        if retry_stats["retried_stations"] > 0:
            print(f"重试统计: {retry_stats['retried_stations']} 个站点进行了重试，共 {retry_stats['total_retries']} 次")
        
        if url_error_list:
            print(f"URL错误站点（前10个）: {url_error_list[:10]}")
        if data_error_list:
            print(f"数据错误站点（前10个）: {data_error_list[:10]}")
    else:
        print("警告: 没有成功下载任何数据！")


def prepare_observation():
    """
    同步包装函数，用于兼容原有接口
    """
    asyncio.run(prepare_observation_async())


def prepare_all():
    os.makedirs(TMP_DIR, exist_ok=True)
    prepare_observation()


if __name__ == "__main__":
    prepare_all()
