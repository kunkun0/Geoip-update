import urllib.request
import netaddr
from mmdb_writer import MMDBWriter

# 选用的纯 IPv4 稳定数据源
SOURCES_TEXT = [
    # 17mon 官方中国 IPv4 列表
    "https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt",
    # 高频同步的中国运营商及专用 IPv4 列表
    "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/ip-lists/china.txt",
]

def fast_merge():
    print("⚡ 开始抓取与整合纯 IPv4 数据源...")
    raw_cidrs = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for url in SOURCES_TEXT:
        try:
            print(f"⏬ 拉取源: {url}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('//'):
                        continue
                    raw_cidrs.append(line)
        except Exception as e:
            print(f"⚠️ 跳过源 ({url}): {e}")

    print(f"📊 收集到原始 IPv4 数据 {len(raw_cidrs)} 条，开始批量解析去重...")

    ip_networks = []
    for cidr in raw_cidrs:
        try:
            net = netaddr.IPNetwork(cidr)
            # 严格过滤，确保只有 IPv4
            if net.version == 4:
                ip_networks.append(net)
        except Exception:
            pass

    # 高速批量去重与相邻网段合并
    cn_ipset = netaddr.IPSet(ip_networks)
    cidrs = cn_ipset.iter_cidrs()
    
    print(f"✅ 整合完成！精简合并为 {len(cn_ipset.iter_cidrs())} 个核心 IPv4 网段。")

    print("🔨 正在写入纯 IPv4 版 GeoIP-CN.mmdb ...")
    writer = MMDBWriter(ip_version=4)

    for cidr in cidrs:
        # mmdb_writer 标准接口规范要求传入 netaddr.IPSet
        writer.insert_network(netaddr.IPSet([cidr]), {'country': {'iso_code': 'CN'}})

    writer.to_db_file("GeoIP-CN.mmdb")
    print("🚀 GeoIP-CN.mmdb 极速构建完成！")

if __name__ == "__main__":
    fast_merge()
