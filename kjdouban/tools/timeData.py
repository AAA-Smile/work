from . import homeData
import pandas as ps
from datetime import datetime
import re

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
    'updated_at'
])


def getTimeList():
    """获取电影年份分布数据"""
    timeList = []
    for date_str in df['release_dates']:
        if date_str and isinstance(date_str, str):
            try:
                # 尝试解析日期字符串，只取年份
                year = date_str[0:4]
                int(year)  # 验证是否为有效年份
                timeList.append(year)
            except (ValueError, TypeError):
                continue
    
    # 统计每个年份的电影数量
    timeData = {}
    for year in timeList:
        if timeData.get(year, -1) == -1:
            timeData[year] = 1
        else:
            timeData[year] = timeData[year] + 1
    
    # 按年份排序
    sorted_items = sorted(timeData.items(), key=lambda x: x[0])
    return [item[0] for item in sorted_items], [item[1] for item in sorted_items]


def getMovieTimeList():
    """获取电影时长分布数据"""
    moveTimeDate = [{
        'name': '短 (<80分钟)',
        'value': 0
    }, {
        'name': '中 (80-120分钟)',
        'value': 0
    }, {
        'name': '长 (120-150分钟)',
        'value': 0
    }, {
        'name': '特长 (>150分钟)',
        'value': 0
    }]
    
    for runtime in df['runtime']:
        if runtime is None or runtime == '':
            continue
        
        # 提取数字
        try:
            # 如果是纯数字字符串
            if isinstance(runtime, (int, float)):
                minutes = int(runtime)
            else:
                # 尝试从字符串中提取数字（如 "142分钟" 或 "1994-09-10" 格式的时长）
                match = re.search(r'\d+', str(runtime))
                if match:
                    minutes = int(match.group())
                else:
                    continue
            
            # 分类统计
            if minutes <= 80:
                moveTimeDate[0]['value'] += 1
            elif minutes <= 120:
                moveTimeDate[1]['value'] += 1
            elif minutes <= 150:
                moveTimeDate[2]['value'] += 1
            else:
                moveTimeDate[3]['value'] += 1
        except (ValueError, TypeError):
            continue
    
    return moveTimeDate


def getReleaseYearData():
    """获取电影年份趋势数据"""
    years = []
    ratings = []
    
    for _, row in df.iterrows():
        try:
            year = row['release_year']
            rating = row['movie_rating']
            
            if year and str(year).isdigit():
                years.append(int(year))
                ratings.append(float(rating) if rating else 0)
        except (ValueError, TypeError):
            continue
    
    return years, ratings
