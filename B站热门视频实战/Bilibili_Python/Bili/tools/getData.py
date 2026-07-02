import pandas as pd
import pymysql

# 数据库配置（与你爬虫中的一致）
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "bilibili",
    "charset": "utf8mb4",
}

# 要导出的表名
TABLE_NAME = "bilibili_videos"   # 或 "movies"

# 建立连接
conn = pymysql.connect(**DB_CONFIG)

# 读取整张表到 DataFrame
df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
conn.close()

# 导出为 CSV（utf-8-sig 让 Excel 正确显示中文）
df.to_csv(f"{TABLE_NAME}.csv", index=False, encoding="utf-8-sig")
print(f"已导出 {TABLE_NAME}.csv，共 {len(df)} 行")

# 如果希望导出为 Excel（需要 openpyxl）
# df.to_excel(f"{TABLE_NAME}.xlsx", index=False)
# print(f"已导出 {TABLE_NAME}.xlsx")