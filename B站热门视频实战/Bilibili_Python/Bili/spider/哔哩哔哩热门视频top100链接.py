"""
功能：抓取 B 站综合热门视频链接（https://www.bilibili.com/v/popular/all）
     默认 100 条，可通过参数调整数量
"""
import argparse
import json
import time
from pathlib import Path
import requests

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.bilibili.com/",
}

def fetch_popular_links(limit=100, delay=1.5):
    """
    从综合热门 API 分页抓取视频链接，每页最多 50 条
    """
    links = []
    page = 1
    while len(links) < limit:
        url = f"https://api.bilibili.com/x/web-interface/popular?pn={page}&ps=50"
        print(f"正在抓取：{url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            data = resp.json()
            if data["code"] != 0:
                print(f"API 返回错误：{data.get('message', '')}")
                break
            for v in data["data"]["list"]:
                bvid = v.get("bvid")
                if bvid:
                    link = f"https://www.bilibili.com/video/{bvid}"
                    if link not in links:
                        links.append(link)
                    if len(links) >= limit:
                        break
            if data["data"].get("no_more"):
                print("已无更多数据")
                break
        except Exception as e:
            print(f"请求失败：{e}")
            break
        page += 1
        time.sleep(delay)
    return links[:limit]

def main():
    parser = argparse.ArgumentParser(description="抓取 B 站综合热门视频链接")
    parser.add_argument("--limit", type=int, default=100, help="需要获取的链接数（默认100）")
    parser.add_argument("--delay", type=float, default=1.5, help="请求间隔（秒）")
    parser.add_argument("--output", default="bilibili_popular_links.txt", help="输出文件名")
    args = parser.parse_args()

    print(f"开始抓取综合热门视频链接，目标数量：{args.limit}")
    links = fetch_popular_links(limit=args.limit, delay=args.delay)
    output_path = OUTPUT_DIR / args.output
    output_path.write_text("\n".join(links), encoding="utf-8")
    print(f"完成！共保存 {len(links)} 条链接到 {output_path}")

if __name__ == "__main__":
    main()