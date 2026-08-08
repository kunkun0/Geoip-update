import urllib.request
import maxminddb
from mmdb_writer import MMDBWriter

GEOIP_URL = "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb"
INPUT_FILE = "geoip_raw.mmdb"
OUTPUT_MMDB = "GeoIP-CN.mmdb"

def build_cn_mmdb():
    print("⏬ 正在下载最新 GeoIP 数据库...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(GEOIP_URL, headers=headers)
    with urllib.request.urlopen(req) as response, open(INPUT_FILE, 'wb') as out_file:
        out_file.write(response.read())

    print("✂️ 开始提取 CN 数据并重新打包为轻量 .mmdb ...")
    reader = maxminddb.open_database(INPUT_FILE)
    writer = MMDBWriter(ip_version=6) # 同时支持 IPv4 和 IPv6

    count = 0
    for network, data in reader:
        if isinstance(data, dict):
            code = data.get('country', {}).get('iso_code') or data.get('registered_country', {}).get('iso_code')
            if code == 'CN':
                # 写入极简的国家代码数据
                writer.insert_network(network, {'country': {'iso_code': 'CN'}})
                count += 1

    reader.close()
    
    # 导出精简版 mmdb
    writer.to_db_file(OUTPUT_MMDB)
    print(f"✅ 成功生成 {OUTPUT_MMDB}！包含 {count} 个 CN 网段。")

if __name__ == "__main__":
    build_cn_mmdb()
