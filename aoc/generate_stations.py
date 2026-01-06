import json
import pymysql
import re
from datetime import datetime

MYSQL_CONFIG = {
    'host': '115.190.81.184',
    'port': 30730,
    'user': 'gnss',
    'password': 'klv!dopY$uN8I',
    'database': 'gnss',
    'charset': 'utf8'
}

def natural_key(s):
    parts = re.split(r'(\d+)', s)
    return [int(p) if p.isdigit() else p.lower() for p in parts]

def generate_stations_json():
    print("开始生成 stations.json ...")

    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    cursor.execute("SELECT ID FROM sb_jbxx")
    rows = cursor.fetchall()

    ids = [row[0] for row in rows]

    # 自然排序
    ids.sort(key=natural_key)

    cursor.close()
    conn.close()

    output_path = "./static/stations.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False, indent=2)

    print(f"生成成功！共 {len(ids)} 个站点。 时间：{datetime.now()}")

if __name__ == "__main__":
    generate_stations_json()
