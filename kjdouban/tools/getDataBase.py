# 这里的数据库信息需要改为自己本机电脑的数据库信息。
import pymysql


def get_conn():
    """
    建立数据库连接
    返回：tuple - (数据库连接对象, 游标对象)
    """
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        database='kjdouban',
        port=3306
    )
    cursor = conn.cursor()
    return conn, cursor
