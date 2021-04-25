from flask import Flask
from flask import request
from flask import render_template
from flask_pymongo import PyMongo
from datetime import datetime
from datetime import timedelta
from bson.objectid import ObjectId
from flask import abort
from flask import redirect
from flask import url_for
from flask import flash
from flask import session
from functools import wraps
import time
import math 

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/myweb"
app.config["SECRET_KEY"] = "abcd"
# 세션 유지시간 설정(30분)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
mongo = PyMongo(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None or session.get("id") == "":
            # next_url에 현재 주소값인 request.url넘겨줌
            return redirect(url_for("member_login", next_url=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.template_filter("formatdatetime")
def format_datetime(value):
    if value is None:
        return ""
    
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    value = datetime.fromtimestamp((int(value) / 1000)) + offset
    return value.strftime('%Y-%m-%d %H:%M:%S')


@app.route("/list")
def lists():
    # 페이지 값(값이 없는 경우 기본값은 1)
    page = request.args.get("page", default=1, type=int)
    # 한 페이지당 몇 개의 게시물을 출력할지
    limit = request.args.get("limit", 7, type=int)

    search = request.args.get("search", -1, type=int)
    keyword = request.args.get("keyword", type=str)

    # 최종적으로 완성된 쿼리를 만들 변수
    query = {}
    # 검색어 상태를 추가할 리스트 변수
    search_list = []

    if search == 0:
        search_list.append({"title": {"$regex" : keyword}})
    elif search == 1:
        search_list.append({"contents": {"$regex" : keyword}})
    elif search == 2:
        search_list.append({"title": {"$regex" : keyword}})       
        search_list.append({"contents": {"$regex" : keyword}})
    elif search == 2:
        search_list.append({"name": {"$regex" : keyword}})       
    
    # 검색 대상이 한개라도 존재할 경우 query 변수에 $or 리스트를 쿼리 함
    if len(search_list) > 0:
        query = {"$or": search_list}
    

    print(query)


    board = mongo.db.board
    datas = board.find(query).skip((page - 1) * limit).limit(limit)

    # 게시물의 총 갯수
    tot_count = board.find(query).count()
    # 마지막 페이지의 수를 구한다.
    last_page_num = math.ceil(tot_count / limit)

    # 페이지 블럭을 5개씩 표기
    block_size = 5
    # 현재 블럭의 위치
    block_num = int((page - 1) / block_size)
    # 블럭의 시작 위치
    block_start = int((block_size * block_num) + 1)
    # 블럭의 끝 위치
    block_last = math.ceil(block_start + (block_size - 1))

    return render_template(
        "list.html",
        datas=datas, 
        limit=limit,
        page=page,
        block_start=block_start,
        block_last=block_last,
        last_page_num=last_page_num,
        search=search,
        keyword=keyword) 


@app.route("/view/<idx>")
@login_required
def board_view(idx):
    # idx = request.args.get("idx")
    if idx is not None:
        page = request.args.get("page")
        search = request.args.get("search")
        keyword = request.args.get("keyword")

        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})

        if data is not None:
            result = {
                "id": data.get("_id"),
                "name": data.get("name"),
                "title": data.get("title"),
                "contents": data.get("contents"),
                "pubdate": data.get("pubdate"),
                "view": data.get("view"),
                "wirter_id": data.get("writer_id", ""),
            }

            return render_template("view.html", result=result, page=page, search=search, keyword=keyword)
    return abort(404)
        


@app.route("/write", methods=["GET", "POST"])
def board_write():
    # 로그인 해야 글 작성 가능
    #if session.get("id") is None:
    #    return redirect(url_for("member_login"))
@login_required
    if request.method == "POST":
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")
        print(name, title, contents)

        current_utc_time = round(datetime.utcnow().timestamp() * 1000)
        board = mongo.db.board
        post = {
            "name": name,
            "title": title,
            "contents": contents,
            "pubdate": current_utc_time,
            "writer_id": session.get("id"),
            "view": 0,
        }

        x = board.insert_one(post)
        print(x.inserted_id)
        return redirect(url_for("board_view", idx = x.inserted_id))
    else:
        return render_template("write.html")


@app.route("/join", methods=["GET", "POST"])
def member_join():
    if request.method == "POST":
        name = request.form.get("name", type=str)
        email = request.form.get("email", type=str)
        pass1 = request.form.get("pass", type=str)
        pass2 = request.form.get("pass2", type=str)

        if name == "" or email == "" or pass1 == "" or pass2 == "":
            flash("입력되지 않은 값이 있습니다.")
            return render_template("join.html") # join으로 다시 복귀
  
        if pass1 != pass2:
            flash("비밀번호가 일치하지 않습니다.")
            return render_template("join.html") # join으로 다시 복귀

        members = mongo.db.members
        cnt = members.find({"email": email}).count()
        if cnt > 0:
            flash("중복된 이메일 주소입니다.")
            return render_template("join.html") # join으로 다시 복귀
        

        current_utc_time = round(datetime.utcnow().timestamp() * 1000)
        post = {
            "name": name,
            "email": email,
            "pass": pass1,
            "joindate": current_utc_time,
            "logintime": "",
            "logincount": 0
        }

        members.insert_one(post)

        return ""
    else:
        return render_template("join.html")


@app.route("/login", methods=["GET", "POST"])
def member_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("pass")
        next_url = request.form.get("next_url")

        members = mongo.db.members
        data = members.find_one({"email": email})

        if data is None:
            flash("회원 정보가 없습니다.")
            # GET메소드로 login.html 재 실행
            return redirect(url_for("member_login"))
        else:
            if data.get("pass") == password:
                session["email"] = email
                session["name"] = data.get("name")
                session["id"] = str(data.get("_id"))
                # 세션 유지시간 설정함
                session.permanent = True
                return redirect(url_for("lists"))
            else:
                flash("비밀번호가 일치하지 않습니다.")
                return redirect(url_for("member_login"))
        return ""
    else:
        next_url = request.args.get("next_url", type=str)
        if next_url is not None:
            return render_template("login.html", next_url=next_url)
        else: 
            return render_template("login.html")

@app.route("/edit/<idx>", methods=["GET", "POST"])
def board_edit(idx):
    return ""


@app.route("/delete/<idx>")
def board_delete(idx):
    return ""

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=9000)
 