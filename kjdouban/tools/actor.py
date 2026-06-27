from . import homeData


def getAllActorMovieNum():
    """获取参演电影数量TOP20的演员"""
    allData = homeData.getAllData()
    ActorMovieNum = {}
    for i in allData:
        for j in i[5]:  # actors 是索引5
            if ActorMovieNum.get(j, -1) == -1:
                ActorMovieNum[j] = 1
            else:
                ActorMovieNum[j] = ActorMovieNum[j] + 1
    ActorMovieNum = sorted(ActorMovieNum.items(), key=lambda x: x[1])[-20:]
    x = []
    y = []
    for i in ActorMovieNum:
        x.append(i[0])
        y.append(i[1])
    return x, y


def getAllDirectorMovieNum():
    """获取执导电影数量TOP20的导演"""
    allData = homeData.getAllData()
    DirectorMovieNum = {}
    for i in allData:
        for j in i[1]:  # directors 是索引1
            if DirectorMovieNum.get(j, -1) == -1:
                DirectorMovieNum[j] = 1
            else:
                DirectorMovieNum[j] = DirectorMovieNum[j] + 1
    DirectorMovieNum = sorted(DirectorMovieNum.items(), key=lambda x: x[1])[-20:]
    x = []
    y = []
    for i in DirectorMovieNum:
        x.append(i[0])
        y.append(i[1])
    return x, y