import pandas as pd
import json

# 读取标签频率表
df = pd.read_csv(R'D:\PythonProject\Bilibili\Bili\tools\Data\标签频率统计（标签出现频率大于等于3的）.csv', encoding='utf-8-sig')

# 转换成列表，每个元素是 {name: 标签, value: 次数}
data = df.to_dict('records')

# 写入一个 JSON 文件，方便 HTML 读取
with open(R'D:\PythonProject\Bilibili\Bili\HTML\Json数据\bubble_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)