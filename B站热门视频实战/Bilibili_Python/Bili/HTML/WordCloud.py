from pyecharts.charts import WordCloud
from pyecharts import options as opts
import pandas as pd

df = pd.read_csv(R'D:\PythonProject\Bilibili\Bili\tools\Data\标签频率统计（标签出现频率大于等于3的）.csv', encoding='utf-8-sig')
data = [(row['标签'], row['出现次数']) for _, row in df.iterrows()]

wc = (
    WordCloud()
    .add(series_name="标签", data_pair=data, word_size_range=[20, 100], shape='circle')
    .set_global_opts(title_opts=opts.TitleOpts(title="标签词云"))
)
wc.render('标签词云.html')
print("交互式词云已保存为 标签词云.html")