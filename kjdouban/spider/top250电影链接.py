import argparse
import os
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


TOP250_URL = "https://movie.douban.com/top250"
OUTPUT_DIR = Path("output")
COOKIE_FILE = Path("cookie.txt")
BASE_DIR = Path(__file__).resolve().parent

# 模拟浏览器请求，降低被豆瓣直接拦截的概率。
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://movie.douban.com/",
    "Connection": "keep-alive",
}


def clean_text(text):
    """清理多余空白字符。"""
    return re.sub(r"\s+", " ", text or "").strip()


def load_cookie(cookie="", cookie_file=""):
    """按命令行、环境变量、cookie.txt 的顺序读取 Cookie。"""
    if cookie:
        return cookie.strip()

    env_cookie = os.getenv("DOUBAN_COOKIE", "").strip()
    if env_cookie:
        return env_cookie

    candidates = []
    if cookie_file:
        candidates.append(Path(cookie_file))
    candidates.extend([Path.cwd() / COOKIE_FILE, BASE_DIR / COOKIE_FILE])

    for path in candidates:
        path = path.resolve()
        if path.exists():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return text
    return ""


def build_headers(cookie):
    """把 Cookie 放入请求头。"""
    headers = HEADERS.copy()
    if cookie:
        headers["Cookie"] = cookie
    return headers


def fetch_html(url, headers):
    """请求网页并返回 HTML。"""
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    return response.text


def is_security_page(html):
    """判断豆瓣是否返回了安全验证页面。"""
    soup = BeautifulSoup(html, "html.parser")
    if soup.select_one("form#sec"):
        return True
    title = soup.title.get_text(strip=True) if soup.title else ""
    return title == "豆瓣" and "载入中" in soup.get_text(" ", strip=True)


def parse_top250_links(html):
    """从 Top250 列表页中提取电影详情页链接。"""
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for node in soup.select(".grid_view .hd a"):
        url = node.get("href", "").strip()
        if url and url not in links:
            links.append(url)

    return links


def get_top250_links(limit, headers, delay):
    """分页抓取 Top250 链接，每页 25 条。"""
    links = []

    for start in range(0, limit, 25):
        page_url = f"{TOP250_URL}?start={start}"
        print(f"正在抓取链接页: {page_url}")

        html = fetch_html(page_url, headers)
        if is_security_page(html):
            raise RuntimeError(f"豆瓣返回安全验证页：{page_url}")

        page_links = parse_top250_links(html)
        if not page_links:
            raise RuntimeError(f"没有解析到电影链接：{page_url}")

        for url in page_links:
            if url not in links:
                links.append(url)
            if len(links) >= limit:
                break

        if len(links) >= limit:
            break

        time.sleep(delay)

    return links


def main():
    parser = argparse.ArgumentParser(description="抓取豆瓣 Top250 电影详情链接并保存到 txt")
    parser.add_argument("--limit", type=int, default=250, help="保存数量，最多 250")
    parser.add_argument("--delay", type=float, default=2.0, help="每页请求后的等待秒数")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="输出目录")
    parser.add_argument("--output-file", default="top250_movie_links.txt", help="链接输出文件名")
    parser.add_argument("--cookie", default="", help="豆瓣 Cookie")
    parser.add_argument("--cookie-file", default="", help="Cookie 文件路径")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    limit = min(max(args.limit, 1), 250)
    headers = build_headers(load_cookie(args.cookie, args.cookie_file))
    links = get_top250_links(limit, headers, args.delay)

    output_file = output_dir / args.output_file
    output_file.write_text("\n".join(links), encoding="utf-8")
    print(f"已保存 {len(links)} 条电影链接到 {output_file}")


if __name__ == "__main__":
    main()