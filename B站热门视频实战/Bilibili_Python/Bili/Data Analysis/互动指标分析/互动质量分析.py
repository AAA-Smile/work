import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False   # 解决负号显示问题

# ========== 1. 数据读取 ==========
# 方式一：从CSV读取（确保字段名一致：play, like, favorite, coin, reply, title, author_name等）
# df = pd.read_csv('bilibili_videos.csv', encoding='utf-8-sig')

# 方式二：从数据库读取（需安装 sqlalchemy + pymysql）
from sqlalchemy import create_engine
engine = create_engine("mysql+pymysql://root:123456@localhost/bilibili?charset=utf8mb4")
df = pd.read_sql("SELECT * FROM bilibili_videos", engine)

# ========== 2. 数据清洗 ==========
# 去除播放量为0的记录
df = df[df['play'] > 0].copy()

# 确保数值列类型正确
for col in ['play', 'like', 'favorite', 'coin', 'reply']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# ========== 3. 计算比值指标 ==========
df['点赞率'] = df['like'] / df['play']
df['收藏率'] = df['favorite'] / df['play']
df['投币率'] = df['coin'] / df['play']
df['评论率'] = df['reply'] / df['play']

# 自定义加权互动总分（权重可调：点赞1, 收藏1.5, 投币2, 评论1）
df['互动总分'] = (df['like'] + 1.5*df['favorite'] + 2*df['coin'] + df['reply']) / df['play']

# ========== 4. 整体分布概览 ==========
print("====== 互动质量指标描述统计 ======")
print(df[['点赞率', '收藏率', '投币率', '评论率', '互动总分']].describe())

# ========== 5. 各指标 Top10 视频 ==========
def show_top10(column, label):
    top = df.nlargest(10, column)[['title', 'play', column, 'author_name']]
    print(f"\n====== {label} Top10 ======")
    print(top.to_string(index=False))
    top.to_csv(f'top10_{label}.csv', index=False, encoding='utf-8-sig')

show_top10('点赞率', '点赞率')
show_top10('收藏率', '收藏率')
show_top10('投币率', '投币率')
show_top10('评论率', '评论率')
show_top10('互动总分', '互动总分')

# ========== 6. 按作者聚合互动质量（视频数≥2） ==========
author_stats = df.groupby('author_name').agg(
    视频数=('title', 'count'),
    平均播放=('play', 'mean'),
    平均点赞率=('点赞率', 'mean'),
    平均收藏率=('收藏率', 'mean'),
    平均投币率=('投币率', 'mean'),
    平均互动总分=('互动总分', 'mean')
).query('视频数 >= 2')

print("\n====== 作者平均互动质量（视频数≥2）Top10 按平均投币率 ======")
print(author_stats.nlargest(10, '平均投币率').to_string())
author_stats.to_csv('作者互动质量.csv', index=True, encoding='utf-8-sig')

# ========== 7. 可视化（示例：播放量与投币率散点图） ==========
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']  # 显示中文
plt.rcParams['axes.unicode_minus'] = False
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='play', y='投币率', alpha=0.5)
plt.xscale('log')
plt.title('播放量与投币率关系')
plt.xlabel('播放量（对数）')
plt.ylabel('投币率')
plt.tight_layout()
plt.savefig('投币率vs播放量.png', dpi=150)
plt.show()

# ========== 8. 保存完整结果 ==========
df.to_csv('bilibili_videos_互动指标.csv', index=False, encoding='utf-8-sig')
print("\n分析完成，已保存文件：bilibili_videos_互动指标.csv, top10_*.csv, 作者互动质量.csv")