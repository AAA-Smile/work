import stylecloud
from tools.getDataBase import get_conn


def getTitleImg(field, icon_name, output_name):
    """
    生成词云图片
    参数：
        field: str - 数据库字段名，用于查询数据
        icon_name: str - stylecloud图标名称（如'fas fa-heart'）
        output_name: str - 输出图片路径
    功能：从数据库读取指定字段数据，生成词云图并保存
    """
    sql = f'select {field} from movies'
    conn, cursor = get_conn()
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    # 将数据转换为逗号分隔的文本
    text1 = ','.join([row[0] for row in data])
    text2 = ','.join(text1)
    # 生成词云
    stylecloud.gen_stylecloud(
        text=text2,
        icon_name=icon_name,
        output_name=output_name,
        font_path='/static/font/simhei.ttf'
    )
