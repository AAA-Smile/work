"""
功能：读取 B 站视频链接文件，批量爬取视频详情（播放量、点赞、收藏、投币、评论、作者、标签等）
"""
import re, time, json
from pathlib import Path
import pymysql
import requests
from bs4 import BeautifulSoup

# ==================== 配置 ====================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "bilibili",
    "charset": "utf8mb4",
}
TABLE_NAME = "bilibili_videos"
LINKS_FILE = R"D:\PythonProject\Bilibili\Bili\spider\output\bilibili_popular_links.txt"  # 改这里
COOKIE_FILE = R"D:\PythonProject\Bilibili\Bili\spider\cookie.txt"
DELAY = 5.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 ...",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.bilibili.com/",
}

def load_cookie():
    try:
        return Path(COOKIE_FILE).read_text(encoding="utf-8").strip()
    except:
        return ""
if load_cookie():
    HEADERS["Cookie"] = load_cookie()

def fetch_json(url, headers):
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()

def read_links():
    links = []
    for line in Path(LINKS_FILE).read_text(encoding="utf-8").splitlines():
        url = line.strip()
        if url and not url.startswith("#") and url not in links:
            links.append(url)
    return links

def extract_bvid(url):
    m = re.search(r"/video/(BV\w+)", url) or re.search(r"(BV\w+)", url)
    return m.group(1) if m else None

def get_fans(mid, headers):
    try:
        data = fetch_json(f"https://api.bilibili.com/x/relation/stat?vmid={mid}", headers)
        return data["data"]["follower"] if data["code"] == 0 else None
    except:
        return None

def parse_video(bvid, headers):
    view_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    view_data = fetch_json(view_url, headers)
    if view_data["code"] != 0:
        raise Exception(f"API错误: {view_data.get('message')}")
    data = view_data["data"]
    stat = data["stat"]
    owner = data["owner"]

    # 标签提取（API + 网页兜底）
    tags = []
    for field in ["tag", "tags", "tag_list", "video_tags"]:
        if field in data:
            raw = data[field]
            if isinstance(raw, list):
                for item in raw:
                    tags.append(item["tag_name"] if isinstance(item, dict) else item)
                break
    tag_str = ",".join(t for t in tags if t)
    if not tag_str:
        try:
            resp = requests.get(f"https://www.bilibili.com/video/{bvid}", headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            panel = soup.select_one(".tag-panel") or soup.select_one(".video-tag")
            if panel:
                tag_str = ",".join(a.get_text(strip=True) for a in panel.select("a"))
        except:
            pass

    fans = get_fans(owner["mid"], headers)
    return {
        "bvid": bvid,
        "title": data["title"],
        "play": stat["view"],
        "like": stat["like"],
        "favorite": stat["favorite"],
        "coin": stat["coin"],
        "reply": stat["reply"],
        "author_name": owner["name"],
        "mid": owner["mid"],
        "fans": fans,
        "tags": tag_str,
        "cover": data.get("pic", ""),
        "duration": data.get("duration", 0),
        "detail_url": f"https://www.bilibili.com/video/{bvid}"
    }

def create_table(conn):
    conn.cursor().execute(f"""CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        bvid VARCHAR(20) UNIQUE NOT NULL,
        title VARCHAR(200),
        play BIGINT DEFAULT 0,
        `like` BIGINT DEFAULT 0,
        favorite BIGINT DEFAULT 0,
        coin BIGINT DEFAULT 0,
        reply BIGINT DEFAULT 0,
        author_name VARCHAR(100),
        mid BIGINT,
        fans BIGINT DEFAULT NULL,
        tags VARCHAR(500),
        cover VARCHAR(500),
        duration INT,
        detail_url VARCHAR(500)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""")
    conn.commit()

def insert_video(conn, v):
    sql = f"""INSERT INTO `{TABLE_NAME}` (bvid,title,play,`like`,favorite,coin,reply,author_name,mid,fans,tags,cover,duration,detail_url)
              VALUES (%(bvid)s,%(title)s,%(play)s,%(like)s,%(favorite)s,%(coin)s,%(reply)s,%(author_name)s,%(mid)s,%(fans)s,%(tags)s,%(cover)s,%(duration)s,%(detail_url)s)
              ON DUPLICATE KEY UPDATE title=VALUES(title),play=VALUES(play),`like`=VALUES(`like`),favorite=VALUES(favorite),
              coin=VALUES(coin),reply=VALUES(reply),author_name=VALUES(author_name),mid=VALUES(mid),fans=VALUES(fans),tags=VALUES(tags),
              cover=VALUES(cover),duration=VALUES(duration),detail_url=VALUES(detail_url);"""
    params = {k: int(v[k]) if k in ("play","like","favorite","coin","reply","mid","fans","duration") and v[k] is not None else v[k] for k in v}
    with conn.cursor() as cur:
        cur.execute(sql, params)
    conn.commit()

def main():
    links = read_links()
    print(f"读取到 {len(links)} 个链接")
    conn = pymysql.connect(**DB_CONFIG)
    create_table(conn)
    ok = fail = 0
    for i, url in enumerate(links, 1):
        bvid = extract_bvid(url)
        if not bvid:
            fail += 1; continue
        print(f"[{i}/{len(links)}] {bvid}")
        try:
            v = parse_video(bvid, HEADERS)
            insert_video(conn, v)
            print(f"  OK: {v['title']}")
            ok += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            fail += 1
        time.sleep(DELAY)
    conn.close()
    print(f"完成：成功{ok}，失败{fail}")

if __name__ == "__main__":
    main()