from . import homeData
import pandas as ps

# 正确的字段顺序要和 homeData.py 保持一致
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


def getAddressData():
    """获取地区数据（只统计单一国家/地区，忽略联合制片），按数量降序排序，返回前15个"""
    addrsses = df['regions'].values
    address = []
    for i in addrsses:
        if isinstance(i, list):
            for j in i:
                j = str(j).strip()
                if j and '/' not in j:
                    address.append(j)
        elif i:
            i = str(i).strip()
            if i and '/' not in i:
                address.append(i)
    
    addressDic = {}
    for i in address:
        if addressDic.get(i, -1) == -1:
            addressDic[i] = 1
        else:
            addressDic[i] = addressDic[i] + 1
    
    sorted_addr = sorted(addressDic.items(), key=lambda x: -x[1])[:15]
    return [item[0] for item in sorted_addr], [item[1] for item in sorted_addr]


def getLangData():
    """获取语言数据（只统计单一语言，忽略混合语言），按数量降序排序，返回前15个"""
    langs = df['languages'].values
    langes = []
    for i in langs:
        if isinstance(i, list):
            for j in i:
                j = str(j).strip()
                if j and '/' not in j:
                    langes.append(j)
        elif i:
            i = str(i).strip()
            if i and '/' not in i:
                langes.append(i)
    
    langsDic = {}
    for i in langes:
        if langsDic.get(i, -1) == -1:
            langsDic[i] = 1
        else:
            langsDic[i] = langsDic[i] + 1
    
    sorted_langs = sorted(langsDic.items(), key=lambda x: -x[1])[:15]
    return [item[0] for item in sorted_langs], [item[1] for item in sorted_langs]
