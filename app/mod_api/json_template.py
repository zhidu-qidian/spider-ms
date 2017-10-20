# coding:utf-8

"""
JSON返回模板
"""

JSON_SUCCESS = {
    "code": 0,
    "msg": "操作成功"
}

JSON_CALL_BACK = {
    "code": 0,
    "msg": "操作成功",
    "data": None
}

JSON_SERVER_ERROR = {
    "code": 1,
    "msg": "服务器内部错误，联系Tacey Wong"
}

JSON_FIELD_LACK = {
    "code": 2,
    "msg": "字段缺失，请检查"
}

JSON_DUP_ERROR = {
    "code": 3,
    "msg": "唯一性冲突，该项目已存在"
}

JSON_NOT_EXIST = {
    "code": 4,
    "msg": "依赖项不存在"
}

JSON_FIELD_UNSUIT = {
    "code": 5,
    "msg": "字段不匹配"
}
