from tools.getDataBase import get_conn


def getCommentTop10():
    """获取评论数TOP10电影数据"""
    sql = 'select title, comment_count from movies order by comment_count desc limit 10'
    conn, cursor = get_conn()
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = []
    for row in data:
        result.append({'name': row[0], 'value': int(row[1])})
    return result


def getStarRatioData():
    """获取电影星级占比数据"""
    sql = 'select star_ratios from movies'
    conn, cursor = get_conn()
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    ratios = {'5星': 0, '4星': 0, '3星': 0, '2星': 0, '1星': 0}
    count = 0
    
    for row in data:
        star_str = row[0]
        if star_str:
            count += 1
            parts = star_str.replace('，', ',').split(',')
            for part in parts:
                part = part.strip()
                if ':' in part:
                    try:
                        key, value = part.split(':', 1)
                        key = key.strip()
                        value = value.strip().replace('%', '')
                        percent = float(value)
                        if key in ratios:
                            ratios[key] += percent
                    except:
                        pass
    
    if count > 0:
        for key in ratios:
            ratios[key] = round(ratios[key] / count, 2)
    
    result = [{'name': k, 'value': v} for k, v in ratios.items()]
    return result


def getReleaseMonthData():
    """获取电影上映月份分布数据"""
    sql = 'select release_dates from movies'
    conn, cursor = get_conn()
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    counts = [0] * 12
    
    for row in data:
        date_str = row[0]
        if date_str:
            try:
                parts = date_str.split('-')
                if len(parts) >= 2:
                    month = int(parts[1]) - 1
                    if 0 <= month < 12:
                        counts[month] += 1
            except:
                pass
    
    result = [{'name': months[i], 'value': counts[i]} for i in range(12)]
    return result