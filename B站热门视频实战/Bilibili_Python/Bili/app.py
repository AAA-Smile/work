import pymysql
import pymysql.cursors
from flask import redirect
from flask import Flask, render_template, jsonify
from collections import Counter
from itertools import combinations

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",      # 改成你的实际密码
    "database": "bilibili",
    "charset": "utf8mb4",
}

def get_conn():
    """建立数据库连接，返回连接和字典游标"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    return conn, cursor

@app.route('/recommend')
def recommend():
    """互动率 Top10 视频推荐"""
    conn, cursor = get_conn()
    sql = """
        SELECT bvid, title, play, `like`, favorite, coin, reply,
               (`like` + 1.5 * favorite + 2 * coin + reply) / play AS interaction_score,
               author_name, 互动总分, detail_url
        FROM bilibili_videos_hu_dong_zhi_biao
        WHERE play > 1000
        ORDER BY interaction_score DESC
        LIMIT 10
    """
    cursor.execute(sql)
    videos = cursor.fetchall()   # 此时 videos 是字典列表
    cursor.close()
    conn.close()
    return render_template('recommend.html', videos=videos)


@app.route('/')
def index():
    return redirect('/recommend')

# ---------- 新增：仪表盘页面 ----------
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ---------- 新增：API 数据接口 ----------

@app.route('/api/top_videos')
def api_top_videos():
    """返回播放/点赞/收藏/投币/评论各自前10的视频"""
    conn, cursor = get_conn()
    metrics = ['play', 'like', 'favorite', 'coin', 'reply']
    result = {}
    for metric in metrics:
        cursor.execute(f"""
            SELECT bvid, title, `{metric}` AS value, author_name
            FROM bilibili_videos
            ORDER BY `{metric}` DESC
            LIMIT 10
        """)
        result[metric] = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/api/duration_ratio')
def api_duration_ratio():
    """返回时长分组的视频数量（环形图）"""
    conn, cursor = get_conn()
    cursor.execute("""
        SELECT
            CASE
                WHEN duration < 300 THEN '<5分钟'
                WHEN duration < 600 THEN '5-10分钟'
                WHEN duration < 1200 THEN '10-20分钟'
                WHEN duration < 1800 THEN '20-30分钟'
                ELSE '>30分钟'
            END AS name,
            COUNT(*) AS value
        FROM bilibili_videos
        GROUP BY name
        ORDER BY FIELD(name, '<5分钟','5-10分钟','10-20分钟','20-30分钟','>30分钟')
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

@app.route('/api/tag_frequency')
def api_tag_frequency():
    """返回标签频率（气泡图）"""
    conn, cursor = get_conn()
    cursor.execute("SELECT tags FROM bilibili_videos WHERE tags IS NOT NULL AND tags != ''")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    from collections import Counter
    counter = Counter()
    for row in rows:
        for tag in row['tags'].split(','):
            tag = tag.strip()
            if tag:
                counter[tag] += 1
    data = [{'name': k, 'value': v} for k, v in counter.items()]
    return jsonify(data)

@app.route('/api/tag_cooccurrence')
def api_tag_cooccurrence():
    """返回标签共现矩阵（前50高频标签）"""
    # 由于需要大量计算，建议在 Python 中预先处理好，这里给出实时计算的逻辑
    conn, cursor = get_conn()
    cursor.execute("SELECT tags FROM bilibili_videos WHERE tags IS NOT NULL AND tags != ''")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    tag_counter = Counter()
    co_counter = Counter()
    for row in rows:
        tags = [t.strip() for t in row['tags'].split(',') if t.strip()]
        tag_counter.update(tags)
        for pair in combinations(sorted(set(tags)), 2):
            co_counter[pair] += 1

    top_tags = [tag for tag, _ in tag_counter.most_common(50)]
    nodes = [{'name': tag} for tag in top_tags]
    links = []
    for (a, b), w in co_counter.items():
        if a in top_tags and b in top_tags:
            links.append({'source': top_tags.index(a), 'target': top_tags.index(b), 'value': w})
    # 添加对角线自身的权重（可选）
    for i, tag in enumerate(top_tags):
        links.append({'source': i, 'target': i, 'value': tag_counter[tag]})
    return jsonify({'nodes': nodes, 'links': links})

@app.route('/api/duration_stats')
def api_duration_stats():
    """返回时长分组的平均播放量及各项互动率"""
    conn, cursor = get_conn()
    cursor.execute("""
        SELECT
            CASE
                WHEN duration < 300 THEN '<5分钟'
                WHEN duration < 600 THEN '5-10分钟'
                WHEN duration < 1200 THEN '10-20分钟'
                WHEN duration < 1800 THEN '20-30分钟'
                ELSE '>30分钟'
            END AS name,
            AVG(play) AS avg_play,
            AVG(`like`/play) AS avg_like_rate,
            AVG(favorite/play) AS avg_fav_rate,
            AVG(coin/play) AS avg_coin_rate,
            AVG(reply/play) AS avg_reply_rate,
            COUNT(*) AS count
        FROM bilibili_videos
        WHERE play > 0
        GROUP BY name
        ORDER BY FIELD(name, '<5分钟','5-10分钟','10-20分钟','20-30分钟','>30分钟')
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)

@app.route('/api/wordcloud_high_play')
def api_wordcloud_high_play():
    """播放量前20视频的标签词频"""
    conn, cursor = get_conn()
    cursor.execute("""
        SELECT tags FROM (
            SELECT tags FROM bilibili_videos ORDER BY play DESC LIMIT 20
        ) t
        WHERE tags IS NOT NULL AND tags != ''
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    counter = Counter()
    for row in rows:
        for tag in row['tags'].split(','):
            tag = tag.strip()
            if tag: counter[tag] += 1
    return jsonify([{'name': k, 'value': v} for k, v in counter.items()])

@app.route('/api/wordcloud_high_interaction')
def api_wordcloud_high_interaction():
    """互动总分前20视频的标签词频"""
    conn, cursor = get_conn()
    cursor.execute("""
        SELECT tags FROM (
            SELECT tags, (`like` + 1.5*favorite + 2*coin + reply)/play AS score
            FROM bilibili_videos
            WHERE play > 0
            ORDER BY score DESC LIMIT 20
        ) t
        WHERE tags IS NOT NULL AND tags != ''
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    counter = Counter()
    for row in rows:
        for tag in row['tags'].split(','):
            tag = tag.strip()
            if tag: counter[tag] += 1
    return jsonify([{'name': k, 'value': v} for k, v in counter.items()])

if __name__ == '__main__':
    app.run(debug=True, port=5000)