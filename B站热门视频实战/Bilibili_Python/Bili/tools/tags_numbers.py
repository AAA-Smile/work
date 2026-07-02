import pandas as pd
#from sqlalchemy import create_engine   # 如果用数据库

# ========== 选择数据源 ==========
# 方式1：从CSV读取
df = pd.read_csv(R'D:\PythonProject\Bilibili\Bili\tools\Data\bilibili_videos.csv', encoding='utf-8-sig')

# 方式2：从MySQL读取
# engine = create_engine("mysql+pymysql://root:123456@localhost:3306/kjdouban?charset=utf8mb4")
# df = pd.read_sql("SELECT tags FROM bilibili_videos", engine)

# ========== 统计标签频率 ==========
# 拆分成单个标签，并去除首尾空格
all_tags = df['tags'].dropna().str.split(',').explode().str.strip()

# 频次统计，降序
tag_counts = all_tags.value_counts().reset_index()
tag_counts.columns = ['标签', '出现次数']

# 保存结果
tag_counts.to_csv('标签频率统计.csv', index=False, encoding='utf-8-sig')

print("分析完成，结果文件：标签频率统计.csv")
print(tag_counts.head(10))   # 打印前10个高频标签