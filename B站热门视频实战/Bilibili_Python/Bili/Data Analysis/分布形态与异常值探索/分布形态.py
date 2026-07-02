import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# ========== 1. 环境设置 ==========
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# ========== 2. 数据读取与清洗 ==========
from sqlalchemy import create_engine
engine = create_engine("mysql+pymysql://root:123456@localhost/bilibili?charset=utf8mb4")
df = pd.read_sql("SELECT * FROM bilibili_videos", engine)

# 确保数值列正确
numeric_cols = ['play', 'like', 'favorite', 'coin', 'reply', 'fans', 'duration']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 去除关键指标缺失或为0的记录
df = df[(df['play'] > 0) & (df['fans'] > 0)].copy()

print(f"有效数据量: {len(df)} 条")

# ========== 3. 长尾分布可视化（直方图） ==========
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 播放量分布（对数变换后仍呈偏态）
ax1 = axes[0]
sns.histplot(df['play'], bins=30, kde=True, ax=ax1, color='steelblue', log_scale=(True, False))
ax1.set_title('播放量分布（对数横轴）', fontsize=14)
ax1.set_xlabel('播放量（对数坐标）')
ax1.set_ylabel('频次')

# 粉丝数分布
ax2 = axes[1]
sns.histplot(df['fans'], bins=30, kde=True, ax=ax2, color='coral', log_scale=(True, False))
ax2.set_title('UP主粉丝数分布（对数横轴）', fontsize=14)
ax2.set_xlabel('粉丝数（对数坐标）')
ax2.set_ylabel('频次')

plt.tight_layout()
plt.savefig('分布形态_直方图.png', dpi=150)
plt.show()

# ========== 4. 箱线图：发现异常值 ==========
metrics_to_plot = ['play', 'like', 'favorite', 'coin', 'reply', 'fans']
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes = axes.flatten()

for i, col in enumerate(metrics_to_plot):
    # 使用对数刻度箱线图，更容易发现极端值
    data = df[col]
    ax = axes[i]
    # 箱线图需要数值，对数变换后绘制
    log_data = np.log10(data[data > 0])
    ax.boxplot(log_data, vert=True, patch_artist=True,
               boxprops=dict(facecolor='lightblue'))
    ax.set_title(f'{col} 对数分布箱线图', fontsize=12)
    ax.set_ylabel(f'log10({col})')
    ax.set_xticklabels([col])
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('分布形态_箱线图.png', dpi=150)
plt.show()

# ========== 5. Z‑score 识别异常值（按指标逐一标记） ==========
# 对于严重偏态的数据，先取对数再进行 Z‑score 标准化
df_zscore = df.copy()
for col in ['play', 'like', 'favorite', 'coin', 'reply', 'fans']:
    # 取对数（避免 log(0) 用一个小值）
    log_col = np.log10(df[col].replace(0, np.nan))
    z_col = np.abs(stats.zscore(log_col, nan_policy='omit'))
    df_zscore[col + '_zscore'] = z_col

# 定义异常条件：任意一个指标的 |Z| > 2.5
outlier_mask = (df_zscore[[c+'_zscore' for c in metrics_to_plot]] > 2.5).any(axis=1)
outliers = df[outlier_mask].copy()
print(f"检测到异常视频数量: {len(outliers)}")

# 打印异常视频的关键信息（标题、播放量、赞、粉丝等）
print("异常视频示例（前10条）：")
print(outliers[['title', 'play', 'like', 'fans']].head(10))

# 保存异常视频列表
outliers.to_csv('异常视频列表.csv', index=False, encoding='utf-8-sig')

# ========== 6. 集中度分析：Top N 占比 ==========
# 按播放量降序排列
df_sorted = df.sort_values('play', ascending=False)
total_play = df_sorted['play'].sum()

# 计算前1、前5、前10、前20视频的播放量占比
top_n_list = [1, 3, 5, 10, 20]
concentration = {}
for n in top_n_list:
    top_sum = df_sorted.head(n)['play'].sum()
    concentration[n] = top_sum / total_play * 100

print("\n===== 播放量集中度 =====")
for k, v in concentration.items():
    print(f"前 {k:2d} 个视频占比: {v:.2f}%")

# 可视化为柱状图
plt.figure(figsize=(8, 5))
bars = plt.bar([str(k) for k in concentration.keys()], list(concentration.values()),
               color='steelblue', edgecolor='black')
plt.title('Top N 视频播放量集中度', fontsize=14)
plt.xlabel('Top N')
plt.ylabel('占总播放量百分比 (%)')
for bar, v in zip(bars, concentration.values()):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{v:.1f}%',
             ha='center', fontsize=11)
plt.ylim(0, max(concentration.values()) * 1.2)
plt.tight_layout()
plt.savefig('集中度分析.png', dpi=150)
plt.show()

# ========== 7. 保存分布统计数据 ==========
desc = df[metrics_to_plot].describe(percentiles=[.25, .5, .75, .9, .95, .99])
desc.to_csv('分布描述统计.csv', encoding='utf-8-sig')
print("\n分布描述统计已保存至 分布描述统计.csv")
print("分析完成。输出文件：分布形态_直方图.png, 分布形态_箱线图.png, 异常视频列表.csv, 集中度分析.png, 分布描述统计.csv")