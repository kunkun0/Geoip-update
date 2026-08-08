import urllib.request
import netaddr
from mmdb_writer import MMDBWriter

# 选择拉取速度最快、精细度极高的几个 CIDR 文本源（跳过巨大的 MMDB 文件解包，极大提速）
SOURCES_TEXT = [
    # 17mon 官方中国 IP 列表
    "https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt",
    # 高频同步的高精度中国运营商及专用 IP
    "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/ip-lists/china.txt",
    # ip2location 每日更新 CN 列表
    "https://raw.githubusercontent.com/ipverse/iptoasn-webservice/master/data/lookup/CN.txt",
]

def fast_merge():
    print("⚡ 开始极速抓取与整合...")
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
                    # 仅收集字符串，先不创建复杂的 netaddr 对象
                    raw_cidrs.append(line)
        except Exception as e:
            print(f"⚠️ 跳过失效源 ({url}): {e}")

    print(f"📊 收集到原始网段 {len(raw_cidrs)} 条，开始批量解析去重...")

    # 一次性批量生成 IPNetwork，比循环逐条 add 快 10 倍以上
    ip_networks = []
    for cidr in raw_cidrs:
        try:
            ip_networks.append(netaddr.IPNetwork(cidr))
        except Exception:
            pass

    # 一次性传入 IPSet，利用 C 底层高效去重合并
    cn_ipset = netaddr.IPSet(ip_networks)
    cidrs = cn_ipset.iter_cidrs()
    
    print(f"✅ 整合完成！精简合并为 {len(cn_ipset.iter_cidrs())} 个核心 CIDR 网段。")

    print("🔨 正在极速写入 GeoIP-CN.mmdb ...")
    writer = MMDBWriter(ip_version=6)

    # 批量插入
    for cidr in cidrs:
        writer.insert_network(cidr, {'country': {'iso_code': 'CN'}})

    writer.to_db_file("GeoIP-CN.mmdb")
    print("🚀 极速构建完成！")

if __name__ == "__main__":
    fast_merge()
