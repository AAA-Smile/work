import json
import pandas as pd

# 1. 读取标签频率 CSV（确保文件名和列名一致）
df = pd.read_csv(R'D:\PythonProject\Bilibili\Bili\tools\Data\标签频率统计（标签出现频率大于等于3的）.csv', encoding='utf-8-sig')

# 2. 将数据转换为列表，每个元素是字典 {name: 标签, value: 出现次数}
#    注意：你 CSV 中的列名可能是 '标签' 和 '出现次数'，如果不一样请修改
data_list = []
for _, row in df.iterrows():
    data_list.append({
        "name": row['标签'],      # 列名可能不同，请核对！
        "value": row['出现次数']  # 列名可能不同，请核对！
    })

# 3. 将数据转为 JSON 字符串（不转义中文）
data_json = json.dumps(data_list, ensure_ascii=False)

# 4. 读取模板文件
with open('template.html', 'r', encoding='utf-8') as f:
    template = f.read()

# 5. 替换占位符
final_html = template.replace('__DATA_PLACEHOLDER__', data_json)

# 6. 写入最终 HTML 文件
output_file = '标签气泡图.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(final_html)

print(f"✅ 生成成功！请双击打开：{output_file}")