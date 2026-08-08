import urllib.request
import netaddr
from mmdb_writer import MMDBWriter

# 筛选稳定、高频更新的文本源
SOURCES_TEXT = [
    # 17mon 官方中国 IP 列表
    "https://raw.githubusercontent.com/17mon/china_ip_list/master/china_ip_list.txt",
    # 高频同步的中国运营商及 IP 列表
    "https://raw.githubusercontent.com/gaoyifan/china-operator-ip/ip-lists/china.txt",
    # ipverse 官方最新 CN IP 列表
    "https://raw.githubusercontent.com/ipverse/iptoasn-webservice/master/data/lookup/CN.tsv",
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
                    # 处理 TSV 格式数据（提取第一列或网段字段）
                    if '\t' in line:
                        parts = line.split('\t')
                        # 如果是 TSV，包含起止 IP 或 CIDR
                        for part in parts:
                            if '/' in part:
                                raw_cidrs.append(part)
                                break
                    else:
                        raw_cidrs.append(line)
        except Exception as e:
            print(f"⚠️ 跳过失效源 ({url}): {e}")

    print(f"📊 收集到原始数据 {len(raw_cidrs)} 条，开始批量解析去重...")

    # 1. 批量生成 IPNetwork 对象
    ip_networks = []
    for cidr in raw_cidrs:
        try:
            ip_networks.append(netaddr.IPNetwork(cidr))
        except Exception:
            pass

    # 2. 一次性构建 IPSet 进行高速合并去重
    cn_ipset = netaddr.IPSet(ip_networks)
    cidrs = cn_ipset.iter_cidrs()
    
    print(f"✅ 整合完成！精简合并为 {len(cn_ipset.iter_cidrs())} 个核心 CIDR 网段。")

    # 3. 构建并写入 MMDB
    print("🔨 正在写入 GeoIP-CN.mmdb ...")
    writer = MMDBWriter(ip_version=6)

    # 关键修复：mmdb-writer 必须接收 netaddr.IPSet 对象
    for cidr in cidrs:
        writer.insert_network(netaddr.IPSet([cidr]), {'country': {'iso_code': 'CN'}})

    writer.to_db_file("GeoIP-CN.mmdb")
    print("🚀 极速构建成功！")

if __name__ == "__main__":
    fast_merge()
