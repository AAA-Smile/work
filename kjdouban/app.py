import time
from flask import Flask, render_template, request
from flask import redirect, url_for, session, jsonify
from tools.actor import getAllActorMovieNum, getAllDirectorMovieNum
from tools.addressData import getAddressData, getLangData
from tools.homeData import *
from tools.rateData import getRate_tType, getStart, getMean, getCountryRating
from tools.timeData import getTimeList, getMovieTimeList
from tools.typeData import getMovieTypeData, getGenreRatingData
from tools.getData import mainFun
from tools.moreData import getCommentTop10, getStarRatioData, getReleaseMonthData
from functools import wraps


# 创建Flask应用，指定静态文件和模板文件路径
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'ywqq'


def login_required(f):
    """登录装饰器：检查用户是否已登录，未登录则重定向到登录页"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 根路由：重定向到登录页
@app.route('/')
def rootRoute():
    return render_template('login.html')

# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册处理"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['passwordCheked']

        if not username or not password:
            return '<h1>用户名和密码不能为空！</h1>'

        if len(password) < 6:
            return '<h1>密码长度至少需要6位！</h1>'

        if password != confirm_password:
            return '<h1>两次密码不一致！</h1>'

        conn, cursor = get_conn()
        try:
            cursor.execute('select username from users')
            data = cursor.fetchall()
            userList = [user[0] for user in data]

            if username in userList:
                return '<h1>用户名已经存在！</h1>'

            cursor.execute('insert into users (username, password) values (%s, %s)', (username, password))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')


# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录处理"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            return redirect(url_for('login'))

        conn, cursor = get_conn()
        try:
            # 使用参数化查询防止SQL注入
            cursor.execute('select * from users where username=%s and password=%s', (username, password))
            user = cursor.fetchone()

            if user:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return redirect(url_for('login'))
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')


# 首页
@app.route('/home')
@login_required
def home():
    """首页：展示电影数据概览和图表"""
    username = session['username']
    allData = getAllData()
    dataLen = len(allData)
    maxRate = getMaxRate()
    maxCast = getMaxCast()
    typeAll = len(getTypesAll())
    maxLang = getMaxLang()
    maxCountry = getMaxCountry()

    types = getType_t()
    x, y = getRate_t()

    return render_template('home.html', username=username,
                           dataLen=dataLen, maxRate=maxRate,
                           maxCast=maxCast, maxCountry=maxCountry,
                           typeAll=typeAll, maxLang=maxLang,
                           types=types, x=list(x), y=list(y))


# 搜索功能
@app.route('/search/<int:serachId>', methods=['GET', 'POST'])
@login_required
def search(serachId):
    """电影搜索功能"""
    username = session['username']
    allData = getAllData()
    data = []
    if request.method == 'GET':
        if serachId == 0:
            return render_template('search.html', username=username, data=data)

        for item in allData:
            if item[0] == serachId:
                data.append(item)
        return render_template('search.html', username=username, data=data)
    else:
        searchWord = request.form['searchIpt']
        if not searchWord:
            return redirect(url_for('search', serachId=serachId))

        def filterFun(item):
            return searchWord in item[3]

        data = list(filter(filterFun, allData))
        return render_template('search.html', username=username, data=data)

if __name__ == '__main__':
    app.run(debug=True)