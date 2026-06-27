"""
功能描述：
    读取电影链接列表，批量爬取豆瓣电影详情页，并将数据保存到MySQL数据库
"""
import re
import time
from pathlib import Path
import pymysql
import requests
from bs4 import BeautifulSoup

# ==================== 配置常量 ====================
"""
数据库连接配置
host: 数据库主机地址（本地为localhost）
user: 数据库用户名
password: 数据库密码
database: 数据库名称
charset: 字符编码（utf8mb4支持表情符号）
"""
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "kjdouban",
    "charset": "utf8mb4",
}

TABLE_NAME = "movies"  # 数据库表名
LINKS_FILE = R"D:\PythonProject\kjdouban\spider\output\top250_movie_links.txt"  # 电影链接文件路径
COOKIE_FILE = R"D:\PythonProject\kjdouban\spider\cookie.txt"  # Cookie文件路径
DELAY = 2.0  # 请求间隔（秒），避免被封
debug_saved = False  # 调试标志：是否已保存调试页面


def load_cookie():
    """
    从文件加载Cookie
    功能：读取cookie.txt文件内容，用于绕过豆瓣反爬验证
    返回：str: Cookie字符串（如果文件存在），否则返回空字符串
    异常处理：FileNotFoundError: Cookie文件不存在时打印警告并返回空字符串
    """
    try:
        # 读取Cookie文件并去除首尾空白
        return Path(COOKIE_FILE).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        print(f"警告：Cookie文件 {COOKIE_FILE} 不存在")
        return ""


"""
HTTP请求头配置
模拟浏览器请求，避免被识别为爬虫：
- User-Agent: 浏览器标识
- Accept: 接受的内容类型
- Accept-Language: 语言偏好
- Referer: 来源页面（伪造访问来源）
"""
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://movie.douban.com/",
}

# 动态加载Cookie到请求头
cookie = load_cookie()
if cookie:
    HEADERS["Cookie"] = cookie


# ==================== 工具函数 ====================

def clean_text(text):
    """
    文本清理函数
    功能：去除文本中的多余空白字符（换行、制表符、多个连续空格）
    参数：text: str - 待清理的文本
    返回：str - 清理后的文本（去除首尾空白，中间多个空格合并为一个）
    """
    return re.sub(r"\s+", " ", text or "").strip()


def fetch_html(url, headers):
    """
    HTTP请求函数
    功能：发送GET请求获取网页内容，处理编码问题
    参数：url: str - 请求的URL地址 headers: dict - 请求头字典
    返回：str - 网页HTML内容
    """
    # 发送GET请求，超时时间20秒
    response = requests.get(url, headers=headers, timeout=20)
    # 检查HTTP状态码，非200则抛出异常
    response.raise_for_status()
    # 处理编码：优先使用响应头中的编码，否则自动检测
    if response.encoding:
        response.encoding = response.encoding
    else:
        response.encoding = response.apparent_encoding
    return response.text


def read_links():
    """
    读取电影链接列表
    功能：从文件中读取链接，去除空行、注释行和重复链接
    返回：list - 去重后的电影链接列表
    文件格式要求：每行一个链接，以 # 开头的行为注释（会被忽略）
        示例：
            https://movie.douban.com/subject/1292052/
            # 这是一条注释
            https://movie.douban.com/subject/1292053/
    """
    links = []
    # 读取文件所有行
    for line in Path(LINKS_FILE).read_text(encoding="utf-8").splitlines():
        url = line.strip()
        # 跳过空行、注释行，并去重
        if url and not url.startswith("#") and url not in links:
            links.append(url)
    return links


# ==================== 页面解析函数 ====================
def parse_movie(url):
    """
    解析电影详情页
    功能：从豆瓣电影详情页提取电影信息
    参数：url: str - 电影详情页URL
    返回：
        dict - 包含电影信息的字典，字段包括：
            directors: 导演（逗号分隔）
            movie_rating: 评分
            title: 标题
            detail_url: 详情页URL
            actors: 主演（逗号分隔，取前3位）
            cover_url: 封面图片URL
            release_year: 上映年份
            genres: 类型（逗号分隔）
            regions: 制片国家/地区
            languages: 语言
            release_dates: 上映时间
            runtime: 影片时长
            comment_count: 评论数
            star_ratios: 星级占比（格式："5星:30%,4星:50%"）
            summary: 简介
            detail_images: 详情图片（逗号分隔，最多4张）
    """
    # 1. 获取页面HTML
    html = fetch_html(url, HEADERS)

    # 2. 检测反爬拦截
    if "安全验证" in html or "检测到异常访问" in html or "请输入验证码" in html:
        raise Exception("被豆瓣安全拦截，请检查Cookie是否有效")

    # 3. 调试：保存第一个页面供分析（仅执行一次）
    global debug_saved
    if not debug_saved:
        debug_saved = True
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html[:5000])  # 只保存前5000字符
        print("  [DEBUG] 已保存调试页面: debug_page.html")

    # 4. 解析HTML
    soup = BeautifulSoup(html, "html.parser")

    # 5. 提取电影标题
    title_selector = soup.select_one("h1 span[property='v:itemreviewed']") or soup.select_one("h1")
    title = clean_text(title_selector.get_text() if title_selector else "")
    # 去除标题中的年份后缀（如 "肖申克的救赎 (1994)" → "肖申克的救赎"）
    title = re.split(r"\s{1,}", title, maxsplit=1)[0] if title else ""

    # 6. 提取上映年份（从标题或年份元素中提取4位数字）
    year_match = re.search(r"\d{4}",
                           clean_text(soup.select_one("span.year").get_text() if soup.select_one("span.year") else ""))
    year = year_match.group(0) if year_match else ""

    # 7. 提取星级占比（5星到1星的百分比）
    star_ratios = []
    for idx, item in enumerate(soup.select(".ratings-on-weight .item"), 1):
        ratio_node = item.select_one(".rating_per")
        if ratio_node:
            # idx从1开始，对应1星到5星，所以用6-idx转换为5星到1星
            star_ratios.append(f"{6 - idx}星:{clean_text(ratio_node.get_text())}")

    # 8. 提取评论数
    comment_count = ""
    comments_section = soup.select_one("#comments-section")
    if comments_section:
        # 匹配"全部 X 条"格式
        match = re.search(r"全部\s*([\d,]+)\s*条", comments_section.get_text())
        if match:
            comment_count = match.group(1).replace(",", "")
    # 如果没找到，尝试从评分人数获取
    if not comment_count:
        comment_count = clean_text(soup.select_one("span[property='v:votes']").get_text() if soup.select_one(
            "span[property='v:votes']") else "")

    # 9. 提取简介
    summary = ""
    # 尝试多个可能的选择器（应对页面结构变化）
    for selector in [
        "#link-report-intra span[property='v:summary']",
        "#link-report span[property='v:summary']",
        ".related-info span[property='v:summary']"
    ]:
        node = soup.select_one(selector)
        if node:
            summary = clean_text(node.get_text())
            break

    # 10. 提取详情图片（最多4张）
    detail_images = []
    for node in soup.select("#related-pic .related-pic-bd img")[:4]:
        img_url = node.get("src", "").strip()
        if img_url and img_url not in detail_images:
            detail_images.append(img_url)

    # 11. 提取影片时长
    runtime = ""
    runtime_node = soup.select_one("span[property='v:runtime']")
    if runtime_node:
        runtime = clean_text(runtime_node.get_text() or runtime_node.get("content", ""))

    # 12. 内部函数：提取info区域的信息（如制片国家、语言等）
    def get_info(label):
        """
        从info区域提取指定标签的内容
        参数：label: str - 标签名称（如"制片国家/地区"、"语言"）
        返回：str - 标签对应的内容
        """
        info = soup.select_one("#info")
        if not info:
            return ""
        for node in info.select("span.pl"):
            # 匹配标签（去除冒号）
            if clean_text(node.get_text()).rstrip(":：") == label.rstrip(":："):
                values = []
                # 获取标签后面的兄弟节点内容
                for sibling in node.next_siblings:
                    if getattr(sibling, "name", None) == "br":
                        break  # 遇到换行符停止
                    # 获取文本内容，处理BeautifulSoup对象和普通字符串
                    text = clean_text(sibling.get_text(" ", strip=True) if hasattr(sibling, "get_text") else sibling)
                    text = text.replace(":", "").replace("：", "")  # 去除多余冒号
                    if text:
                        values.append(text)
                return clean_text(" ".join(values))
        return ""

    # 13. 构建返回字典
    return {
        "directors": ",".join(clean_text(n.get_text()) for n in soup.select("a[rel='v:directedBy']")),
        "movie_rating": clean_text(soup.select_one("strong[property='v:average']").get_text() if soup.select_one(
            "strong[property='v:average']") else ""),
        "title": title,
        "detail_url": url,
        "actors": ",".join(clean_text(n.get_text()) for n in soup.select("a[rel='v:starring']")[:3]),  # 只取前3位主演
        "cover_url": soup.select_one("#mainpic img").get("src", "").strip() if soup.select_one("#mainpic img") else "",
        "release_year": year,
        "genres": ",".join(clean_text(n.get_text()) for n in soup.select("span[property='v:genre']")),
        "regions": get_info("制片国家/地区"),
        "languages": get_info("语言"),
        "release_dates": clean_text(
            soup.select_one("span[property='v:initialReleaseDate']").get_text() if soup.select_one(
                "span[property='v:initialReleaseDate']") else ""),
        "runtime": runtime or get_info("片长"),  # 优先用v:runtime，否则用info中的片长
        "comment_count": comment_count,
        "star_ratios": "，".join(star_ratios),
        "summary": summary,
        "detail_images": ",".join(detail_images),
    }


# ==================== 数据存储函数 ====================

def insert_movie(connection, movie):
    """
    插入电影数据到数据库
    功能：将解析后的电影数据插入数据库，支持重复数据更新（通过detail_url唯一约束）
    参数：
        connection: pymysql.connections.Connection - 数据库连接对象
        movie: dict - 电影信息字典（parse_movie返回的结果）
    SQL特点：
        - 使用 INSERT ... ON DUPLICATE KEY UPDATE 语法
        - 当detail_url已存在时，更新所有字段（实现增量更新）
        - 使用参数化查询（%s占位符）防止SQL注入
    类型转换：
        - movie_rating: str → float（空值转为None）
        - comment_count: str → int（去除逗号后转换，空值转为None）
    """
    # SQL插入语句（支持重复更新）
    sql = f"""
    INSERT INTO `{TABLE_NAME}` (
        directors, movie_rating, title, detail_url, actors, cover_url,
        release_year, genres, regions, languages, release_dates, runtime,
        comment_count, star_ratios, summary, detail_images
    ) VALUES (
        %(directors)s, %(movie_rating)s, %(title)s, %(detail_url)s, %(actors)s, %(cover_url)s,
        %(release_year)s, %(genres)s, %(regions)s, %(languages)s, %(release_dates)s, %(runtime)s,
        %(comment_count)s, %(star_ratios)s, %(summary)s, %(detail_images)s
    ) ON DUPLICATE KEY UPDATE
        directors=VALUES(directors), movie_rating=VALUES(movie_rating), title=VALUES(title),
        actors=VALUES(actors), cover_url=VALUES(cover_url), release_year=VALUES(release_year),
        genres=VALUES(genres), regions=VALUES(regions), languages=VALUES(languages),
        release_dates=VALUES(release_dates), runtime=VALUES(runtime), comment_count=VALUES(comment_count),
        star_ratios=VALUES(star_ratios), summary=VALUES(summary), detail_images=VALUES(detail_images);
    """

    # 构建参数字典（进行类型转换）
    params = {
        "directors": movie["directors"],
        "movie_rating": float(movie["movie_rating"]) if movie["movie_rating"] else None,
        "title": movie["title"],
        "detail_url": movie["detail_url"],
        "actors": movie["actors"],
        "cover_url": movie["cover_url"],
        "release_year": movie["release_year"],
        "genres": movie["genres"],
        "regions": movie["regions"],
        "languages": movie["languages"],
        "release_dates": movie["release_dates"],
        "runtime": movie["runtime"],
        "comment_count": int(movie["comment_count"].replace(",", "")) if movie["comment_count"] else None,
        "star_ratios": movie["star_ratios"],
        "summary": movie["summary"],
        "detail_images": movie["detail_images"],
    }

    # 执行SQL
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
    # 提交事务
    connection.commit()


# ==================== 主函数 ====================

def main():
    """
    爬虫主函数
    功能：调度整个爬取流程
    流程：
        1. 读取电影链接列表
        2. 建立数据库连接
        3. 循环爬取每个电影页面
        4. 解析页面并保存到数据库
        5. 输出爬取结果统计
    异常处理：
        - 单个电影爬取失败不影响其他电影
        - 数据库连接在finally块中确保关闭
    """
    # 1. 读取链接列表
    links = read_links()
    print("=" * 50)
    print("【开始爬取豆瓣电影数据】")
    print(f"读取到 {len(links)} 个电影链接")
    print("=" * 50)

    # 2. 建立数据库连接
    connection = pymysql.connect(**DB_CONFIG)

    try:
        # 3. 初始化统计变量
        success = 0  # 成功数量
        failed = 0  # 失败数量

        # 4. 循环爬取
        for index, url in enumerate(links, 1):
            print(f"[{index}/{len(links)}] {url}")
            try:
                # 解析电影页面
                movie = parse_movie(url)
                # 保存到数据库
                insert_movie(connection, movie)
                # 输出成功信息
                print(f"  OK: {movie['title']}")
                success += 1
            except Exception as e:
                # 单个电影失败，记录并继续
                print(f"  FAIL: {str(e)[:100]}")
                failed += 1
            # 5. 请求间隔（反爬措施）
            time.sleep(DELAY)

    finally:
        # 6. 确保关闭数据库连接
        connection.close()
        print("\n【数据库连接已关闭】")

    # 7. 输出统计结果
    print("\n=== 爬取完成 ===")
    print(f"成功: {success} 部")
    print(f"失败: {failed} 部")
    print(f"成功率: {success / len(links) * 100:.1f}%")


# 程序入口
if __name__ == "__main__":
    main()