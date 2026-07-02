import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter

# ========== 1. 环境设置 ==========
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False

# ========== 2. 读取数据 ==========
df = pd.read_csv(R'D:\PythonProject\Bilibili\Bili\Data Analysis\互动指标分析\bilibili_videos_互动指标.csv', encoding='utf-8-sig')

# ========== 4. 筛选互动总分前10的视频 ==========
top10 = df.nlargest(10, '互动总分')

# ========== 5. 合并标签并统计词频 ==========
all_tags = []
for tags_str in top10['tags'].dropna():
    # 按逗号拆分，去除空格和空字符串
    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
    all_tags.extend(tags)

tag_counts = Counter(all_tags)

# 打印前10高频词
print("Top10视频的标签频率：")
for tag, count in tag_counts.most_common(10):
    print(f"{tag}: {count}")

# ========== 6. 绘制词云 ==========
# 生成词云（字体路径请根据系统修改，这里使用系统默认中文字体）
wc = WordCloud(
    font_path='simhei.ttf',   # 若无此字体，可替换为 'C:/Windows/Fonts/msyh.ttc' 等
    width=800,
    height=600,
    background_color='white',
    max_words=100,
    colormap='viridis'
).generate_from_frequencies(tag_counts)

plt.figure(figsize=(10, 8))
plt.imshow(wc, interpolation='bilinear')
plt.axis('off')
plt.title('互动总分Top10视频标签词云', fontsize=16)
plt.tight_layout()
plt.savefig('互动总分Top10视频标签词云.png', dpi=150)
plt.show()

# ========== 7. 可选：保存词频表 ==========
pd.DataFrame(tag_counts.items(), columns=['标签', '频次']).to_csv('Top10标签频次.csv', index=False, encoding='utf-8-sig')
print("词云已保存为 互动总分Top10视频标签词云.png，词频表已保存为 Top10标签频次.csv")