# from setuptools import setup, find_packages

# setup(
#     name="its_app",
#     version="0.1.0",
#     packages=find_packages(),
#     install_requires=[
#         "fastapi",
#         "uvicorn",
#         "python-dotenv",
#         "pydantic",
#         "pydantic-settings",
#         "openai",
#         "openai-agents",
#         "pymysql",
#         "dbutils",
#         "pystun3"
#     ],
# )
import stun

# 依次尝试的 STUN 服务器列表
# 注意：pystun3 默认用的 stun.l.google.com 在国内网络不可达；
# 部分国内 STUN 服务器的 UDP 3478 也会被网络/防火墙拦截
STUN_HOSTS = [
    "stun.m-online.net",
    "stun.stunprotocol.org",
    "stun.miwifi.com",
    "stun.qq.com",
]


def get_ip_via_stun():
    # 使用 STUN 协议获取公网 IP（UDP 3478）
    # 逐个尝试列表中的 STUN 服务器，返回第一个成功的
    for host in STUN_HOSTS:
        try:
            nat_type, external_ip, _ = stun.get_ip_info(stun_host=host)
        except Exception:
            continue
        if external_ip:
            print(f"  NAT 类型: {nat_type}（来自 {host}）")
            return external_ip
    return None


def get_ip_via_http():
    # STUN 的 UDP 端口被网络/防火墙挡住时的降级方案：
    # 直接请求 HTTP IP 回显服务。这些服务看到的出口 IP
    # 与百度地图等 HTTP 服务实际收到的出口 IP 一致，更可靠
    import httpx

    services = ["https://ipinfo.io/ip", "https://ifconfig.me/ip"]
    for url in services:
        try:
            ip = httpx.get(url, timeout=10).text.strip()
            if ip:
                print(f"  （HTTP 降级，来源: {url}）")
                return ip
        except Exception:
            continue
    return None


if __name__ == "__main__":
    public_ip = get_ip_via_stun()
    if not public_ip:
        print("STUN 全部失败，切换 HTTP 方式")
        public_ip = get_ip_via_http()
    print(f"Public IP: {public_ip}")
