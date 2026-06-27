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


def getMovieTypeData():
    """获取电影类型数据"""
    types = df['genres'].values
    type_list = []
    for i in types:
        if isinstance(i, list):
            for j in i:
                j = str(j).strip()
                if j:
                    type_list.append(j)
        elif i:
            i = str(i).strip()
            if i:
                type_list.append(i)
    
    typeDic = {}
    for i in type_list:
        if typeDic.get(i, -1) == -1:
            typeDic[i] = 1
        else:
            typeDic[i] = typeDic[i] + 1
    
    result = []
    for key, value in typeDic.items():
        result.append({
            'name': key,
            'value': value
        })
    
    return result


def getGenreRatingData():
    """获取各类型电影的平均评分"""
    genre_ratings = {}
    
    for _, row in df.iterrows():
        genres = row['genres']
        rating = row['movie_rating']
        
        if not genres or not rating:
            continue
        
        try:
            rating = float(rating)
        except (ValueError, TypeError):
            continue
        
        if isinstance(genres, list):
            for genre in genres:
                genre = str(genre).strip()
                if genre:
                    if genre not in genre_ratings:
                        genre_ratings[genre] = []
                    genre_ratings[genre].append(rating)
        else:
            genre = str(genres).strip()
            if genre:
                if genre not in genre_ratings:
                    genre_ratings[genre] = []
                genre_ratings[genre].append(rating)
    
    result = []
    for genre, ratings in genre_ratings.items():
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            result.append({
                'name': genre,
                'value': round(avg_rating, 2),
                'count': len(ratings)
            })
    
    # 按评分排序
    result.sort(key=lambda x: -x['value'])
    return result
