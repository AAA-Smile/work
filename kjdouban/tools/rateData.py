import re
from numpy import *
import pandas as ps
from . import homeData

df = ps.DataFrame(homeData.getAllData(), columns=[
    'id',
    'directors',
    'movie_rating',
    'title',
    'detail_url',
    'actors',
    'cover_url',
    'release_year',
    'genres',
    'regions',
    'languages',
    'release_dates',
    'runtime',
    'comment_count',
    'star_ratios',
    'summary',
    'detail_images',
    'created_at',
    'updated_at',
])


def getRate_tType(type):
    """获取特定类型电影的评分分布"""
    allData = homeData.getAllData()
    rateList = []
    for i in allData:
        if i[8] and type in i[8]:
            rateList.append(str(i[2]))
    rateForm = {}
    for rating in rateList:
        if rateForm.get(rating, -1) == -1:
            rateForm[rating] = 1
        else:
            rateForm[rating] = rateForm[rating] + 1
    return list(rateForm.keys()), list(rateForm.values())


def getStart(movieName):
    """获取电影的星级占比"""
    if not movieName:
        movie_data = df.iloc[0]
    else:
        matching = df[df['title'].str.contains(movieName, na=False)]
        if matching.empty:
            movie_data = df.iloc[0]
        else:
            movie_data = matching.iloc[0]
    
    searchName = movie_data['title']
    star_ratios = movie_data['star_ratios']
    
    startList = [
        {'name': '五星', 'value': 0},
        {'name': '四星', 'value': 0},
        {'name': '三星', 'value': 0},
        {'name': '二星', 'value': 0},
        {'name': '一星', 'value': 0},
    ]
    
    star_str = ''
    if star_ratios:
        if isinstance(star_ratios, list) and len(star_ratios) > 0:
            star_str = star_ratios[0]
        elif isinstance(star_ratios, str):
            star_str = star_ratios
    
    if star_str:
        matches = re.findall(r'(\d+)星:(\d+\.?\d*)', star_str)
        for star, value in matches:
            star_idx = 5 - int(star)
            if 0 <= star_idx < 5:
                startList[star_idx]['value'] = float(value)
    
    return startList, searchName


def getCountryRating():
    """获取各国家/地区的电影数量和平均评分"""
    allData = homeData.getAllData()
    data = [
        {'name': '中国', 'count': 0, 'rating': []},
        {'name': '美国', 'count': 0, 'rating': []},
        {'name': '英国', 'count': 0, 'rating': []},
        {'name': '韩国', 'count': 0, 'rating': []},
        {'name': '日本', 'count': 0, 'rating': []},
        {'name': '法国', 'count': 0, 'rating': []},
        {'name': '总和', 'count': 0, 'rating': []},
    ]
    
    for i in allData:
        data[-1]['count'] = data[-1]['count'] + 1
        try:
            data[-1]['rating'].append(float(i[2]))
        except (ValueError, TypeError):
            continue
        
        regions = i[9] if i[9] else []
        for region in regions:
            for j in data[:-1]:
                if region and j['name'] in region:
                    j['count'] = j['count'] + 1
                    try:
                        j['rating'].append(float(i[2]))
                    except (ValueError, TypeError):
                        continue
    
    x = []
    y = []
    y22 = []
    for i in data:
        if i['rating']:
            i['rating'] = mean(i['rating'])
        else:
            i['rating'] = 0
        x.append(i['name'])
        y.append(i['count'])
        y22.append(round(i['rating'], 2))
    return x, y, y22


def getMean():
    """获取各年份电影的平均评分（只显示最近10年）"""
    allData = homeData.getAllData()
    meanList = {}
    
    for i in allData:
        year = i[7]
        rating = i[2]
        
        if not year or not rating:
            continue
        
        try:
            year_str = str(year)
            if meanList.get(year_str, -1) == -1:
                meanList[year_str] = [float(rating)]
            else:
                meanList[year_str].append(float(rating))
        except (ValueError, TypeError):
            continue
    
    meanList = sorted(meanList.items(), key=lambda x: x[0])
    rows = []
    columns = []
    for year, ratings in meanList:
        rows.append(year)
        columns.append(round(mean(ratings), 2))
    
    if len(rows) > 10:
        rows = rows[-10:]
        columns = columns[-10:]
    
    return rows, columns


def getAllRatingDistribution():
    """获取所有电影的评分分布"""
    allData = homeData.getAllData()
    rating_counts = {}
    
    for i in allData:
        rating = i[2]
        if rating:
            try:
                rating_str = str(rating)
                if rating_counts.get(rating_str, -1) == -1:
                    rating_counts[rating_str] = 1
                else:
                    rating_counts[rating_str] += 1
            except (ValueError, TypeError):
                continue
    
    sorted_ratings = sorted(rating_counts.items(), key=lambda x: float(x[0]))
    return [item[0] for item in sorted_ratings], [item[1] for item in sorted_ratings]
