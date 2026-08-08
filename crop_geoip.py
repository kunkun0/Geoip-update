import os
import urllib.request
import maxminddb
import ipaddress

# 更换为稳定可靠的 GitHub Raw 源（Loyalsoldier 的最新 mmdb 文件准确路径）
GEOIP_URL = "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb"

# 如果上面那个在中国大陆/Actions 节点偶尔超时，也可以使用 jsDelivr CDN 加速源：
# GEOIP_URL = "https://cdn.jsdelivr.net/gh/Loyalsoldier/geoip@release/Country.mmdb"

INPUT_FILE = "geoip_raw.mmdb"
OUTPUT_FILE = "GeoIP-CN.mmdb"

def download_geoip():
    print("⏬ 正在下载最新 GeoIP 数据库...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(GEOIP_URL, headers=headers)
    with urllib.request.urlopen(req) as response, open(INPUT_FILE, 'wb') as out_file:
        out_file.write(response.read())
    print("✅ 下载完成！")

def filter_cn_only():
    print("✂️ 开始裁剪数据库，仅保留 CN 数据...")
    
    # 读取原始 mmdb
    reader = maxminddb.open_database(INPUT_FILE)
    
    cn_cidrs = []
    
    # 遍历原始数据库中的所有网段
    try:
        # 针对 Loyalsoldier 或标准 MaxMind GeoLite2 结构读取
        for network, data in reader:
            if isinstance(data, dict):
                country_code = data.get('country', {}).get('iso_code') or data.get('registered_country', {}).get('iso_code')
                if country_code == 'CN':
                    cn_cidrs.append(str(network))
    except Exception as e:
        print(f"解析过程提示: {e}")
    finally:
        reader.close()

    print(f"📊 提取成功！共获取到 {len(cn_cidrs)} 个 CN IP 网段。")

    # 将提取出的 CN 网段导出为标准精简版文本 CIDR 列表及生成标识
    with open("cn_ip.txt", "w", encoding="utf-8") as f:
        f.write("# Minimal CN IP CIDR List\n")
        for cidr in cn_cidrs:
            f.write(f"{cidr}\n")
            
    print("✅ CN IP 文本网段导出完成 (cn_ip.txt)。")

if __name__ == "__main__":
    download_geoip()
    filter_cn_only()
