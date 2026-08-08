import urllib.request
import ipaddress
import maxminddb
from mmdb_writer import MMDBWriter

# 1. 多个权威数据源 (包含 MMDB 与 txt CIDR 列表)
SOURCES_TEXT = [
    # ipverse 每日更新的中国 IPv4 & IPv6 列表
    "https://raw.githubusercontent.com/ipverse/iptoasn-webservice/master/data/lookup/CN.txt",
    # 极简高精度的中国 IP 网段文本
    "https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt",
]

SOURCES_MMDB = [
    # Loyalsoldier 的 Country.mmdb
    "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb",
    # P3TERX 维护的 GeoLite2 Country 源
    "https://raw.githubusercontent.com/P3TERX/GeoLite.mmdb/download/GeoLite2-Country.mmdb",
]

def fetch_and_merge():
    cn_networks = set()
    headers = {'User-Agent': 'Mozilla/5.0'}

    # ---- A. 从文本源拉取 CIDR ----
    for url in SOURCES_TEXT:
        try:
            print(f"⏬ 正在拉取文本数据源: {url}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('//'):
                        continue
                    try:
                        net = ipaddress.ip_network(line, strict=False)
                        cn_networks.add(net)
                    except ValueError:
                        pass
            print(f"  -> 当前已累计 {len(cn_networks)} 个网段")
        except Exception as e:
            print(f"⚠️ 拉取失败 ({url}): {e}")

    # ---- B. 从 MMDB 源提取 CN 网段 ----
    for idx, url in enumerate(SOURCES_MMDB):
        tmp_file = f"tmp_{idx}.mmdb"
        try:
            print(f"⏬ 正在拉取 MMDB 数据源: {url}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp, open(tmp_file, 'wb') as f:
                f.write(resp.read())

            reader = maxminddb.open_database(tmp_file)
            for network, data in reader:
                if isinstance(data, dict):
                    code = data.get('country', {}).get('iso_code') or data.get('registered_country', {}).get('iso_code')
                    if code == 'CN':
                        cn_networks.add(network)
            reader.close()
            print(f"  -> 当前已累计 {len(cn_networks)} 个网段")
        except Exception as e:
            print(f"⚠️ 解析失败 ({url}): {e}")

    print(f"\n📊 整合完成！共去重汇总 {len(cn_networks)} 个 CN IP 网段。")

    # ---- C. 打包编译为标准的 GeoIP-CN.mmdb ----
    print("🔨 正在写入并构建 GeoIP-CN.mmdb ...")
    writer = MMDBWriter(ip_version=6)

    for net in cn_networks:
        writer.insert_network(net, {'country': {'iso_code': 'CN'}})

    writer.to_db_file("GeoIP-CN.mmdb")
    print("✅ 纯净多源整合版 GeoIP-CN.mmdb 构建成功！")

if __name__ == "__main__":
    fetch_and_merge()
