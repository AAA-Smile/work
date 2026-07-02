import pandas as pd
import numpy as np
from itertools import combinations
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False   # 解决负号显示问题

# ========== 1. 数据读取 ==========
# 方式一：从CSV读取（假设有 'tags' 列，标签以逗号分隔）
# df = pd.read_csv('bilibili_videos.csv', encoding='utf-8-sig')

# 方式二：从数据库读取
from sqlalchemy import create_engine
engine = create_engine("mysql+pymysql://root:123456@localhost/bilibili?charset=utf8mb4")
df = pd.read_sql("SELECT tags FROM bilibili_videos", engine)

# ========== 2. 标签预处理 ==========
# 去除空标签，按逗号拆分为列表
tag_lists = df['tags'].dropna().str.split(',').apply(lambda lst: [t.strip() for t in lst if t.strip()])

# 筛选至少有两个标签的视频（否则无法共现）
tag_lists = tag_lists[tag_lists.apply(len) >= 2]

# ========== 3. 统计共现对 ==========
co_occurrence_counter = Counter()
tag_freq = Counter()  # 单个标签出现次数（用于筛选高频标签）

for tags in tag_lists:
    # 统计单个标签频率
    for t in tags:
        tag_freq[t] += 1
    # 生成所有两两组合（无序）
    for pair in combinations(sorted(set(tags)), 2):
        co_occurrence_counter[pair] += 1

print(f"共生成 {len(co_occurrence_counter)} 对标签组合")

# 将共现对转换为 DataFrame
co_df = pd.DataFrame([
    {'source': pair[0], 'target': pair[1], 'weight': count}
    for pair, count in co_occurrence_counter.items()
])

# ========== 4. 筛选高频标签，缩小矩阵规模 ==========
# 取出现次数前 N 的标签（避免矩阵过大）
top_n = 50
top_tags = [tag for tag, _ in tag_freq.most_common(top_n)]

# 过滤共现对：两个标签都在 top_n 中
filtered_co = co_df[co_df['source'].isin(top_tags) & co_df['target'].isin(top_tags)]

# ========== 5. 构建共现矩阵 ==========
# 创建标签索引
all_tags = sorted(set(filtered_co['source']) | set(filtered_co['target']))
tag_index = {tag: i for i, tag in enumerate(all_tags)}
n = len(all_tags)
matrix = np.zeros((n, n), dtype=int)

for _, row in filtered_co.iterrows():
    i, j = tag_index[row['source']], tag_index[row['target']]
    matrix[i, j] = row['weight']
    matrix[j, i] = row['weight']  # 对称矩阵

# ========== 6. 可视化：共现矩阵热力图 ==========
plt.figure(figsize=(14, 12))
sns.heatmap(matrix, xticklabels=all_tags, yticklabels=all_tags,
            cmap='YlOrRd', square=True, linewidths=0.5,
            annot=True, fmt='d', annot_kws={'size': 6})
plt.title('标签共现矩阵（前50高频标签）', fontsize=16)
plt.tight_layout()
plt.savefig('标签共现矩阵.png', dpi=150)
plt.show()

# ========== 7. 可视化：力导向网络图 ==========
# 创建图
G = nx.Graph()
# 添加节点（大小表示频率）
for tag in all_tags:
    G.add_node(tag, weight=tag_freq[tag])

# 添加边（粗度表示共现次数）
for _, row in filtered_co.iterrows():
    G.add_edge(row['source'], row['target'], weight=row['weight'])

plt.figure(figsize=(16, 16))
pos = nx.spring_layout(G, k=0.5, iterations=50)  # 力导向布局

# 节点大小与标签频率成正比
node_sizes = [G.nodes[tag]['weight'] * 2 for tag in G.nodes]
# 边宽度与共现次数成正比
edge_weights = [G[u][v]['weight'] for u, v in G.edges]
edge_widths = [w / max(edge_weights) * 5 for w in edge_weights]

nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='skyblue', alpha=0.8)
nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.3, edge_color='grey')
nx.draw_networkx_labels(G, pos, font_size=8, font_family='sans-serif')

plt.title('标签共现网络图（前50高频标签）', fontsize=16)
plt.axis('off')
plt.savefig('标签共现网络图.png', dpi=150, bbox_inches='tight')
plt.show()

# ========== 8. 导出结果 ==========
filtered_co.to_csv('标签共现关系.csv', index=False, encoding='utf-8-sig')
print(f"分析完成。共现关系已保存至 标签共现关系.csv")