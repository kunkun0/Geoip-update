import urllib.request
import maxminddb
import netaddr
from mmdb_writer import MMDBWriter

# 1. 替换为稳定高频更新的源 (移除失效的 ipverse 链接)
SOURCES_TEXT = [
    # 17mon 官方维护的中国 IP 列表
    "https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt",
    # gfwlist / 社区高频同步的 CN IP 列表
    "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/ip-lists/china.txt",
]

SOURCES_MMDB = [
    # Loyalsoldier 的 Country.mmdb
    "https://raw.githubusercontent.com/Loyalsoldier/geoip/release/Country.mmdb",
    # P3TERX 维护的 GeoLite2 源
    "https://raw.githubusercontent.com/P3TERX/GeoLite.mmdb/download/GeoLite2-Country.mmdb",
]

def fetch_and_merge():
    # 使用 IPSet 可以自动合并重叠的子网，性能极高且天生去重
    cn_ipset = netaddr.IPSet()
    headers = {'User-Agent': 'Mozilla/5.0'}

    # ---- A. 处理文本源 ----
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
                        cn_ipset.add(netaddr.IPNetwork(line))
                    except Exception:
                        pass
            print(f"  -> 当前累计包含 {len(cn_ipset.iter_cidrs())} 个 IP 网段")
        except Exception as e:
            print(f"⚠️ 拉取失败 ({url}): {e}")

    # ---- B. 处理 MMDB 源 ----
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
                        # 将 maxminddb 返回的网络转为 netaddr 对象追加进 IPSet
                        cn_ipset.add(netaddr.IPNetwork(str(network)))
            reader.close()
            print(f"  -> 当前累计包含 {len(cn_ipset.iter_cidrs())} 个 IP 网段")
        except Exception as e:
            print(f"⚠️ 解析失败 ({url}): {e}")

    cidrs = cn_ipset.iter_cidrs()
    print(f"\n📊 整合去重完成！最终生成 {len(cidrs)} 个标准 CIDR 网段。")

    # ---- C. 打包编译为标准的 GeoIP-CN.mmdb ----
    print("🔨 正在写入并构建 GeoIP-CN.mmdb ...")
    writer = MMDBWriter(ip_version=6)

    # 正确转换类型：mmdb_writer 接收 netaddr 的 IPNetwork / IPSet
    for cidr in cidrs:
        writer.insert_network(cidr, {'country': {'iso_code': 'CN'}})

    writer.to_db_file("GeoIP-CN.mmdb")
    print("✅ 纯净多源整合版 GeoIP-CN.mmdb 构建成功！")

if __name__ == "__main__":
    fetch_and_merge()
