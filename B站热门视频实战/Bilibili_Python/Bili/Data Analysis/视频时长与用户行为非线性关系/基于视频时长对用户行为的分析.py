import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# ========== 1. 数据读取 ==========
from sqlalchemy import create_engine
engine = create_engine("mysql+pymysql://root:123456@localhost/bilibili?charset=utf8mb4")
df = pd.read_sql("SELECT * FROM bilibili_videos", engine)

# ========== 2. 数据清洗 ==========
# 确保数值列正确
for col in ['play', 'like', 'favorite', 'coin', 'reply', 'duration']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 去除播放量为0或时长为空的记录
df = df[(df['play'] > 0) & (df['duration'].notna())].copy()

# 将秒转换为分钟便于可视化
df['duration_min'] = df['duration'] / 60

# 计算互动指标
df['点赞率'] = df['like'] / df['play']
df['收藏率'] = df['favorite'] / df['play']
df['投币率'] = df['coin'] / df['play']
df['评论率'] = df['reply'] / df['play']
df['互动总分'] = (df['like'] + 1.5*df['favorite'] + 2*df['coin'] + df['reply']) / df['play']

# ========== 3. 时长分组统计 ==========
bins = [0, 5, 10, 20, 30, float('inf')]
labels = ['<5分钟', '5-10分钟', '10-20分钟', '20-30分钟', '>30分钟']
df['时长分组'] = pd.cut(df['duration_min'], bins=bins, labels=labels, right=False)

# 分组计算平均互动指标
group_stats = df.groupby('时长分组').agg(
    视频数=('title', 'count'),
    平均播放=('play', 'median'),  # 用中位数减少极端值影响
    平均点赞率=('点赞率', 'median'),
    平均收藏率=('收藏率', 'median'),
    平均投币率=('投币率', 'median'),
    平均评论率=('评论率', 'median'),
    平均互动总分=('互动总分', 'median')
).reset_index()

print("====== 时长分组互动指标 ======")
print(group_stats)

# ========== 4. 可视化：分组对比柱状图 ==========
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
metrics = ['平均点赞率', '平均收藏率', '平均投币率', '平均评论率']
for ax, metric in zip(axes.flatten(), metrics):
    ax.bar(group_stats['时长分组'], group_stats[metric], color='skyblue', edgecolor='black')
    ax.set_title(metric, fontsize=14)
    ax.set_xlabel('时长分组')
    ax.set_ylabel(metric)
    ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('时长分组互动指标.png', dpi=150)
plt.show()

# ========== 5. 散点图 + 非线性拟合 ==========
# 为了看清关系，过滤掉极端异常值（如播放量前1%或者时长过长）
q_duration = df['duration_min'].quantile(0.99)
q_metric = df['投币率'].quantile(0.99)
filtered_df = df[(df['duration_min'] <= q_duration) & (df['投币率'] <= q_metric)]

plt.figure(figsize=(12, 5))

# 左图：散点图 + LOWESS 平滑
plt.subplot(1, 2, 1)
sns.scatterplot(data=filtered_df, x='duration_min', y='投币率', alpha=0.5)
# 使用 seaborn 的 regplot 添加 LOWESS
sns.regplot(data=filtered_df, x='duration_min', y='投币率', scatter=False,
            lowess=True, line_kws={'color': 'red', 'lw': 2})
plt.title('视频时长 vs 投币率 (LOWESS 平滑)')
plt.xlabel('视频时长（分钟）')
plt.ylabel('投币率')

# 右图：箱线图看分组分布
plt.subplot(1, 2, 2)
order = ['<5分钟', '5-10分钟', '10-20分钟', '20-30分钟', '>30分钟']
sns.boxplot(data=df, x='时长分组', y='投币率', order=order, palette='Set2')
plt.title('不同时长分组的投币率分布')
plt.xlabel('时长分组')
plt.ylabel('投币率')
plt.tight_layout()
plt.savefig('时长与投币率关系.png', dpi=150)
plt.show()

# ========== 6. 统计检验：Kruskal-Wallis 检验（多组独立样本） ==========
groups = [df[df['时长分组'] == cat]['投币率'].dropna().values for cat in labels]
h_stat, p_val = stats.kruskal(*groups)
print(f"\nKruskal-Wallis 检验 (投币率 vs 时长分组): H={h_stat:.2f}, p={p_val:.4f}")
if p_val < 0.05:
    print("结论：不同时长分组的投币率存在显著差异")
else:
    print("结论：不同时长分组的投币率没有显著差异")

# ========== 7. 保存分组数据 ==========
group_stats.to_csv('时长分组互动指标.csv', index=False, encoding='utf-8-sig')
print("\n分析完成，已保存文件：时长分组互动指标.csv, 时长分组互动指标.png, 时长与投币率关系.png")