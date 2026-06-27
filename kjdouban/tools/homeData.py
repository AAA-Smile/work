import json
import pandas as ps
from tools.getDataBase import get_conn


def getAllData():
    """获取所有电影数据并进行预处理"""
    def map_fn(item):
        item = list(item)
        
        # 处理评分
        if item[2] == None:
            item[2] = 0.0
        else:
            try:
                item[2] = float(item[2])
            except (ValueError, TypeError):
                item[2] = 0.0
        
        # 处理导演
        if item[1] == None:
            item[1] = '无'
        else:
            item[1] = str(item[1]).split(',')
        
        # 处理演员
        if item[5] == None:
            item[5] = '无'
        else:
            item[5] = str(item[5]).split(',')
        
        # 处理类型
        try:
            item[8] = item[8].split(',')
        except Exception as e:
            item[8] = '剧情'
        
        # 处理地区
        if item[9] == None:
            item[9] = '中国大陆'
        else:
            item[9] = item[9].split(',')
        
        # 处理语言
        if item[10] == None:
            item[10] = '汉语普通话'
        else:
            item[10] = item[10].split(',')
        
        # 处理星级占比
        if item[14] == None:
            item[14] = []
        elif isinstance(item[14], str):
            item[14] = item[14].split(',')
        else:
            item[14] = []
        
        # 处理详情图片
        if item[16] == None:
            item[16] = []
        elif isinstance(item[16], str):
            item[16] = item[16].split(',')
        else:
            item[16] = []
        
        return item

    conn, cursor = get_conn()
    cursor.execute('select * from movies')
    allData = cursor.fetchall()
    allData = list(map(map_fn, list(allData)))
    return allData


# 电影数据DataFrame
df = ps.DataFrame(getAllData(), columns=[
    'id', 'directors', 'movie_rating', 'title', 'detail_url',
    'actors', 'cover_url', 'release_year', 'genres', 'regions',
    'languages', 'release_dates', 'runtime', 'comment_count',
    'star_ratios', 'summary', 'detail_images', 'created_at', 'updated_at'
])


def getMaxRate():
    """获取最高评分"""
    return df['movie_rating'].astype(float).max()


def getMinRate():
    """获取最低评分"""
    return df['movie_rating'].astype(float).min()


def getMaxCast():
    """获取参演电影最多的演员"""
    allData = getAllData()
    casts = {}
    maxName = ''
    maxNum = 0
    for i in allData:
        for j in i[5]:
            if casts.get(j, -1) == -1:
                casts[j] = 1
            else:
                casts[j] = casts[j] + 1
    for k, v in casts.items():
        if int(v) > maxNum:
            maxNum = v
            maxName = k
    return maxName


def getMaxLang():
    """获取使用最多的语言"""
    allData = getAllData()
    langs = {}
    maxLang = ''
    maxNum = 0
    for i in allData:
        for j in i[10]:
            if langs.get(j, -1) == -1:
                langs[j] = 1
            else:
                langs[j] = langs[j] + 1
    for k, v in langs.items():
        if int(v) > maxNum:
            maxNum = v
            maxLang = k
    return maxLang


def getMaxCountry():
    """获取制片最多的国家/地区"""
    allData = getAllData()
    countries = {}
    maxCountry = ''
    maxNum = 0
    for i in allData:
        for j in i[9]:
            if countries.get(j, -1) == -1:
                countries[j] = 1
            else:
                countries[j] = countries[j] + 1
    for k, v in countries.items():
        if int(v) > maxNum:
            maxNum = v
            maxCountry = k
    return maxCountry


def getTypesAll():
    """获取所有电影类型"""
    allData = getAllData()
    types = {}
    for i in allData:
        for j in i[8]:
            if types.get(j, -1) == -1:
                types[j] = 1
            else:
                types[j] = types[j] + 1
    return types.keys()


def getType_t():
    """获取电影类型统计数据（用于饼图）"""
    allData = getAllData()
    types = {}
    for i in allData:
        for j in i[8]:
            if types.get(j, -1) == -1:
                types[j] = 1
            else:
                types[j] = types[j] + 1
    data = []
    for k, v in types.items():
        data.append({'name': k, 'value': v})
    return data


def getRate_t():
    """获取电影评分分布数据"""
    allData = getAllData()
    rates = {}
    for i in allData:
        rating = str(i[2])
        if rates.get(rating, -1) == -1:
            rates[rating] = 1
        else:
            rates[rating] = rates[rating] + 1
    return list(rates.keys()), list(rates.values())


def getTableList():
    """获取电影列表数据（用于表格展示）"""
    def map_fn(item):
        item[1] = '/'.join(item[1])   # directors
        item[5] = '/'.join(item[5])   # actors
        item[8] = '/'.join(item[8])   # genres
        item[9] = '/'.join(item[9])   # regions
        item[10] = '/'.join(item[10]) # languages
        return item

    allData = list(getAllData())
    allData = map(map_fn, allData)
    return list(allData)