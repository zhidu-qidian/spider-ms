# coding:utf-8

"""
Token生成及权限验证装饰器
"""

from functools import wraps
from flask import request, redirect, jsonify
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
from config import SECRET_KEY
from app.mylog import logging


class User(object):
    """用户密码验证及token生成"""
    NAME = "qdzx"
    PW = "qidian@lieying"

    @classmethod
    def verify_password(cls, name, pw):
        """验证密码"""
        if name == cls.NAME and pw == cls.PW:
            return True
        return False

    @classmethod
    def gen_token(cls, user, pw, expiration=1440 * 7 * 60):  # 秒, 30天过期
        """生成token"""
        token_s = Serializer(SECRET_KEY, expires_in=expiration)
        return token_s.dumps({'name': user, "pw": pw})

    @classmethod
    def is_login(cls):
        """根据cookie判断是否登陆"""
        result = False
        token = request.cookies.get('token')
        if not token:
            token = request.form.get("token")
        if not token:
            return False
        token_s = Serializer(SECRET_KEY)
        try:
            ver_info = token_s.loads(token)
            user = ver_info.get("name", "")
            pw = ver_info.get("pw", "")
            result = cls.verify_password(user, pw)
        except SignatureExpired as e:
            logging.warning(e)
            result = False
        except BadSignature as e:
            logging.warning(e)
            result = False
        except Exception as e:
            logging.warning(e)
            result = False
        return result


def token_required_html(func):
    """
    token验证装饰器（用于html）
    :param func:
    :return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == "POST":
            name = request.form.get("name")
            pw = request.form.get("pw")
            if name and pw:
                name = str(name).strip()
                pw = str(pw).strip()
                check_result = User.verify_password(name, pw)
                if check_result:
                    token = User.gen_token(name, pw)
                    kwargs['name'] = name
                    kwargs['token'] = token
                    return func(*args, **kwargs)
            return redirect("/login")
        token = request.cookies.get('token')
        if not token:
            token = request.form.get('token')
        if not token:
            return redirect("/login")
        check_result = User.is_login()
        if not check_result:
            return redirect("/login")
        else:
            return func(*args, **kwargs)

    return wrapper


def token_required_json(func):
    """
    token验证装饰器（用于json api）
    :param func:
    :return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        check_result = User.is_login()
        if not check_result:
            return jsonify({'status': 'fail', 'data': {'msg': 'token!token!token!'}})
        else:
            return func(*args, **kwargs)

    return wrapper


if __name__ == "__main__":
    token_test = User.gen_token("tacey")
    token_s_test = Serializer(SECRET_KEY)
    print token_s_test.loads(token_test)
