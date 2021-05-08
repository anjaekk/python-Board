from functools import wraps
from main import session, redirect, request, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None or session.get("id") == "":
            # next_url에 현재 주소값인 request.url넘겨줌
            return redirect(url_for("member.member_login", next_url=request.url))
        return f(*args, **kwargs)
    return decorated_function

