# coding:utf-8

"""
API视图（全部需要token验证）:
    添加网站、修改网站、删除网站
    添加频道、修改频道、删除频道
    获取二级分类信息

"""
import re
import json
import copy
import datetime
import requests
from flask import Blueprint
from flask import request
from flask import jsonify
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
from app.auth import token_required_json
from app.mylog import logging
from app.utils.oss import upload_file_to_oss
from app.utils.general import Encoder
from app.utils.general import url_to_dic
from app.utils.general import str_to_header
from app.utils.general import get_today
from app.utils.general import rebuild_url
from app.utils.db import pg_sql
from app.mod_api.json_template import *
from app import mongo_p, mongo_t

mod_api = Blueprint('api', __name__, url_prefix='/api')


@mod_api.route("/add_site/", methods=["POST"])
@token_required_json
def add_site(**kwargs):
    """
    添加一级源接口（网站etc）
    :return:
    """

    def insert_text(**kw):
        insert_doc = {
            "domain": domain,
            "name": name,
            "description": desc,
            "priority": priority,
            "icon": icon_url
        }
        try:
            mongo_t.db.spider_sites.insert(insert_doc)
            return "OK"
        except DuplicateKeyError:
            return jsonify(JSON_DUP_ERROR)

    def insert_file(**kw):
        icon_file = request.files.get("icon-file")
        if icon_file:
            file_mime = icon_file.mimetype
            icon_url = upload_file_to_oss(file_mime, icon_file.read())
        else:
            icon_url = request.form.get("icon-url", "")
        try:
            mongo_t.db.spider_sites.update({"domain": domain},
                                           {"$set": {"icon": icon_url}})
            return "OK"
        except Exception as e:
            logging.warning(e)
            return jsonify(JSON_SERVER_ERROR)

    domain = request.form.get("domain")
    name = request.form.get("name")
    desc = request.form.get("desc")
    priority = int(request.form.get("priority", "5"))
    icon_url = ""
    if not domain or not name:
        return jsonify(JSON_FIELD_LACK)
    result = insert_text(domain=domain, name=name, desc=desc,
                         priority=priority, icon_url=icon_url)
    if result != "OK":
        return result
    result = insert_file(domain=domain)
    if result != "OK":
        return result
    return jsonify(JSON_SUCCESS)


@mod_api.route("/modify_site/", methods=["POST"])
@token_required_json
def modify_site(**kwargs):
    """
    修改一级源接口（网站etc）
    :return:
    """

    def update_text(**kw):
        update_doc = {
            "name": name,
            "description": desc,
            "priority": priority,
        }
        try:
            mongo_t.db.spider_sites.update({"domain": domain}, {"$set": update_doc})
            return "OK"
        except Exception as e:
            logging.warning(e)
            return jsonify(JSON_SERVER_ERROR)

    def update_file(**kw):
        icon_file = request.files.get("icon-file")
        if icon_file:
            file_mime = icon_file.mimetype
            icon_url = upload_file_to_oss(file_mime, icon_file.read())
        else:
            icon_url = request.form.get("icon-url", "")
        try:
            mongo_t.db.spider_sites.update({"domain": domain},
                                           {"$set": {"icon": icon_url}})
            return "OK"
        except Exception as e:
            logging.warning(e)
            return jsonify(JSON_SERVER_ERROR)

    domain = request.form.get("domain")
    name = request.form.get("name")
    desc = request.form.get("desc")
    priority = int(request.form.get("priority", "5"))
    if not name:
        return jsonify(JSON_FIELD_LACK)
    result = update_text(domain=domain, name=name,
                         desc=desc, priority=priority)
    if result != "OK":
        return result
    result = update_file()
    if result != "OK":
        return result
    return jsonify(JSON_SUCCESS)


@mod_api.route("/remove_site/", methods=["GET"])
@token_required_json
def remove_site(**kwargs):
    """
    移除一级源接口（同时会移除下属各频道及相应配置）
    :return:
    """
    domain = request.args.get("domain", "").strip()
    site = list(mongo_t.db.spider_sites.find({"domain": domain}, {"_id": 1}))
    if not site:
        return jsonify(JSON_NOT_EXIST)
    sid = site[0].get("_id", "")
    channels = list(mongo_t.db.spider_channels.find({"site": str(sid)}))
    for channel in channels:
        cid = channel["_id"]
        mongo_t.db.qidian_map.remove({"channel": str(cid)}, multi=True)
        mongo_t.db.spider_configs.remove({"channel": str(cid)})
        mongo_t.db.spider_channels.remove({"_id": cid})
    mongo_t.db.spider_sites.remove({"_id": sid})
    return jsonify(JSON_SUCCESS)


@mod_api.route("/add_channel/", methods=["POST"])
@token_required_json
def add_channel(**kwargs):
    """
    添加二级数据源（网站频道、微信账号etc）
    :return:
    """
    domain = request.form.get("domain", "").strip()
    cname = request.form.get("cname", "").strip()
    media_type = request.form.get("media_type", "news").strip()
    priority = int(request.form.get("priority", 5))
    cate1 = request.form.get("cate1", 0)
    cate2 = request.form.get("cate2", 0)
    target_type = request.form.getlist("target_type")
    target_type = "#".join(target_type)
    if cate1 == "0":
        cate1 = ""
        cate2 = ""
    elif cate2 == "0":
        cate2 = ""
    desc = request.form.get("desc", "").strip()
    crawler = request.form.get("crawler", "").strip()
    url = request.form.get("url", "").strip()
    headers = request.form.get("headers", "").strip()
    if headers:
        headers = str_to_header(headers)
    else:
        headers = dict()

    params = request.form.get("params", "").strip().strip("?").strip("&")
    if params:
        params = url_to_dic(params)
    else:
        params = dict()
    method = request.form.get("method")
    ua_type = request.form.get("ua_type")

    rules = request.form.get("rules", "")
    rules = [rule for rule in rules.strip().split("#")]
    is_sch = request.form.get("is_sch")
    is_sch = True if is_sch == "1" else False

    author = request.form.get("author", "")
    biz = request.form.get("biz", "")
    certification = request.form.get("certification", "")

    check_site = list(mongo_t.db.spider_sites.find({"domain": domain}))
    if not check_site:
        return jsonify(JSON_NOT_EXIST)
    else:
        site = str(check_site[0]["_id"])
    if not cname:
        return jsonify(JSON_FIELD_LACK)

    insert_cha_doc = {
        "category1": cate1,
        "category2": cate2,
        "name": cname,
        "form": media_type,
        "description": desc,
        "priority": priority,
        "site": site,
        "schedule": is_sch,
        "config": [],
        "status": 0,
        "meta": {
            "name": author,
            "_biz": biz,
            "certification": certification
        }
    }
    try:
        cid = mongo_t.db.spider_channels.insert(insert_cha_doc)
    except DuplicateKeyError:
        return jsonify(JSON_DUP_ERROR)
    except Exception as e:
        logging.warning(e)
        return jsonify(JSON_SERVER_ERROR)
    icon_file = request.files.get("icon-file")
    if icon_file:
        file_mime = icon_file.mimetype
        icon_url = upload_file_to_oss(file_mime, icon_file.read())
    else:
        icon_url = request.form.get("icon-url", "")
    try:
        mongo_t.db.spider_channels.update({"site": site, "name": cname},
                                          {"$set": {"icon": icon_url}})
    except Exception as e:
        logging.warning(e)
        return jsonify(JSON_SERVER_ERROR)

    insert_conf_doc = {
        "channel": str(cid),
        "rules": rules,
        "request": {
            "url": url,
            "method": method,
            "user_agent_type": ua_type,
            "params": params,
            "headers": headers
        },
        "crawler": crawler,
    }

    try:
        conf_id = mongo_t.db.spider_configs.insert(insert_conf_doc)
    except Exception as e:
        logging.warning(e)
        return jsonify(JSON_SERVER_ERROR)
    try:
        mongo_t.db.spider_channels.update({"_id": cid}, {"$push": {"config": str(conf_id)}})
    except Exception as e:
        logging.warning(e)
        return jsonify(JSON_SERVER_ERROR)

    qd_cate1 = int(request.form.get("qd_cate1", 0))
    qd_cate2 = int(request.form.get("qd_cate2", 0))
    if qd_cate1 == 0:
        qd_cate1 = None
    if qd_cate2 == 0:
        qd_cate2 = None
    qidian_map = {
        "first_cid": qd_cate1,
        "second_cid": qd_cate2,
        "channel": str(cid),
        "online": True,
        "type": target_type
    }
    try:
        mongo_t.db.qidian_map.insert(qidian_map)
    except Exception as e:
        logging.warning(e)
        return jsonify(JSON_SERVER_ERROR)

    return jsonify(JSON_SUCCESS)


@mod_api.route("/modify_channel/", methods=["POST"])
@token_required_json
def modify_channel(**kwargs):
    """
    修改二级频道接口（网站频道、微信公众号etc)
    :return:
    """
    cid = request.form.get("cid", "").strip()
    cname = request.form.get("cname", "").strip()
    media_type = request.form.get("media_type", "news").strip()
    priority = int(request.form.get("priority", 5))
    cate1 = request.form.get("cate1")
    cate2 = request.form.get("cate2")
    qd_cate1 = int(request.form.get("qd_cate1", 0))
    qd_cate2 = int(request.form.get("qd_cate2", 0))
    target_type = request.form.getlist("target_type")
    target_type = "#".join(target_type)
    if cate1 == "0":
        cate1 = ""
        cate2 = ""
    elif cate2 == "0":
        cate2 = ""
    if qd_cate1 == 0:
        qd_cate1 = None
        qd_cate2 = None
    elif qd_cate2 == 0:
        qd_cate2 = None
    map_info = {
        "first_cid": qd_cate1,
        "second_cid": qd_cate2,
        "type": target_type
    }

    desc = request.form.get("desc", "").strip()
    crawler = request.form.get("crawler", "").strip()
    url = request.form.get("url", "")
    headers = request.form.get("headers", "").strip()
    if headers:
        headers = str_to_header(headers)
    else:
        headers = dict()

    params = request.form.get("params", "").strip().strip("&").strip("?")
    if params:
        params = url_to_dic(params)
    else:
        params = dict()
    method = request.form.get("method")
    ua_type = request.form.get("ua_type")

    rules = request.form.get("rules", "").strip()
    rules = [rule for rule in rules.strip().split("#")]
    is_sch = request.form.get("is_sch")
    is_sch = True if is_sch == "1" else False

    author = request.form.get("author", "")
    biz = request.form.get("biz", "")
    certification = request.form.get("certification", "")

    if not cname:
        return jsonify(JSON_FIELD_LACK)

    update_cha_doc = {
        "category1": cate1,
        "category2": cate2,
        "name": cname,
        "form": media_type,
        "description": desc,
        "priority": priority,
        "schedule": is_sch,
        "meta": {
            "name": author,
            "_biz": biz,
            "certification": certification
        }
    }
    try:
        mongo_t.db.spider_channels.update({"_id": ObjectId(cid)}, {"$set": update_cha_doc})
    except Exception as e:
        logging.warning(e)
        return jsonify(JSON_SERVER_ERROR)

    try:
        mongo_t.db.qidian_map.update({"channel": str(cid)}, {"$set": map_info})
    except Exception as e:
        logging.warning(e)
        return jsonify(JSON_SERVER_ERROR)

    icon_file = request.files.get("icon-file")
    if icon_file:
        file_mime = icon_file.mimetype
        icon_url = upload_file_to_oss(file_mime, icon_file.read())
    else:
        icon_url = request.form.get("icon-url", "")
        if icon_url == "None":
            icon_url = ""
    try:
        mongo_t.db.spider_channels.update({"_id": ObjectId(cid)},
                                          {"$set": {"icon": icon_url}})
    except Exception as e:
        logging.warning(e)
        return jsonify(JSON_SERVER_ERROR)

    update_conf_doc = {
        "rules": rules,
        "request": {
            "url": url,
            "method": method,
            "user_agent_type": ua_type,
            "params": params,
            "headers": headers
        },
        "crawler": crawler
    }

    try:
        mongo_t.db.spider_configs.update_one({"channel": str(cid)}, {"$set": update_conf_doc})
    except Exception as e:
        logging.warning(e)
        return jsonify(JSON_SERVER_ERROR)
    return jsonify(JSON_SUCCESS)


@mod_api.route("/remove_channel/", methods=['GET'])
@token_required_json
def remove_channel(**kwargs):
    """
    移除二级数据源接口（同时会删除相应配置）
    :return:
    """
    cid = request.args.get("id", "").strip()
    try:
        mongo_t.db.qidian_map.remove({"channel": cid}, multi=True)
        mongo_t.db.spider_configs.remove({"channel": cid}, multi=True)
        mongo_t.db.spider_channels.remove({"_id": ObjectId(cid)})
    except Exception as e:
        logging.warning(e)
        return jsonify(JSON_SERVER_ERROR)
    return jsonify(JSON_SUCCESS)


@mod_api.route("/get_cate2", methods=["POST", "GET"])
@token_required_json
def get_cate2(**kwargs):
    """
    根据一级分类获取二级分类（用于前端分类列表的动态级联）
    :return:
    """
    if request.method == "POST":
        parent = request.form.get("parent")
    else:
        parent = request.args.get("parent")
    if parent:
        json_data = list(mongo_t.db.data_category_two.find({"parent": parent}, {"_id": 0, "parent": 0}))
    else:
        json_data = []
    json_data = {"code": 0, "data": [item["name"] for item in json_data]}
    return jsonify(json_data)


@mod_api.route("/get_qd_cate2", methods=["POST", "GET"])
@token_required_json
def get_qd_cate2(**kwargs):
    """
    根据一级分类获取二级分类（用于前端分类列表的动态级联）
    :return:
    """
    if request.method == "POST":
        chid = request.form.get("chid")
    else:
        chid = request.args.get("chid")
    if chid:
        sql = "select id,cname from sechannellist_v2 where chid=%s;" % chid
        result = pg_sql(sql)
    else:
        result = []
    json_data = []
    for item in result:
        one_item = {
            "id": item[0],
            "name": item[1].decode("utf-8")
        }
        json_data.append(one_item)
    json_data = {"code": 0, "data": json_data}
    return jsonify(json_data)


@mod_api.route("/db_query/", methods=["POST"])
@token_required_json
def db_query(**kwargs):
    """
    库表查询（仅支持thirdparty）
    :return:
    """
    col = request.form.get("collection")
    condition = request.form.get("condition", {})
    sort_c = request.form.get("sort", {"_id": -1})
    limit_c = int(request.form.get("limit", 1))
    if not condition:
        condition = dict()
    else:
        condition = eval(condition)
    if not sort_c:
        sort_c = [("_id", -1)]
    else:
        tmp = []
        try:
            for k, v in eval(sort_c).items():
                tmp.append((k, v))
        except:
            resp = copy.deepcopy(JSON_SERVER_ERROR)
            resp["msg"] = "排序规则有误，请检查"
            return jsonify(resp)
        sort_c = tmp
    try:
        result = list(mongo_t.db[col].find(condition).sort(sort_c).limit(limit_c))
    except Exception as e:
        resp = copy.deepcopy(JSON_SERVER_ERROR)
        resp["msg"] = str(e)
        return jsonify(resp)
    return json.dumps(result, cls=Encoder)


@mod_api.route("/set_schedule", methods=["POST"])
@token_required_json
def set_schedule(**kwargs):
    cid = request.form.get("cid", "0" * 12)
    action = request.form.get("action", "")
    if action == "set_true":
        action = True
    elif action == "set_false":
        action = False
    else:
        return jsonify({"msg": "error,action not surport"})
    mongo_t.db.spider_channels.update({"_id": ObjectId(cid)}, {"$set": {"schedule": action}})
    return jsonify({"result": action, "cid": cid, "msg": "success"})


@mod_api.route("/schedule", methods=["POST", "DELETE"])
@token_required_json
def schedule(**kwargs):
    def get_configs(_id, name="site", schedule=None):
        assert name == "site" or name == "channel"
        if name == "channel":
            query = {"_id": ObjectId(_id), "status": 0}
        else:
            query = {"site": _id, "status": 0}
        if schedule is not None:
            query["schedule"] = schedule
        channels = mongo_t.db.spider_channels.find(query, projection={"_id": 1})
        ids = [str(channel["_id"]) for channel in channels]
        query = {"channel": {"$in": ids}}
        configs = mongo_t.db.spider_configs.find(query)
        return list(configs)

    def post(**kw):
        configs = get_configs(_id, name, schedule=True)
        added = list()
        invalid = list()
        for config in configs:
            channel_id = config["channel"]
            requests.delete(schedule_service_url, data={"id": channel_id})
            id = str(config["_id"])
            for rule in config["rules"]:
                data = {"id": id, "rule": rule, "struct": "set",
                        "key": schedule_cache_key, "value": id}
                doc = requests.post(schedule_service_url, data=data).json()
                if doc["code"] == 200:
                    added.append(id)
                else:
                    invalid.append(id)
        post_result = {"added": str(added), "invalid params": invalid}
        return post_result

    def delete(**kw):
        configs = get_configs(_id, name)
        removed = list()
        miss = list()
        for config in configs:
            id = str(config["_id"])
            doc = requests.delete(schedule_service_url, data={"id": id}).json()
            if doc["code"] == 200:
                removed.append(id)
            else:
                miss.append(id)
        delete_result = {"removed": str(removed), "not found": miss}
        return delete_result

    schedule_service_url = "http://10.25.60.218:9000/tasks"
    schedule_cache_key = "v1:spider:schedule:all:id"
    name = request.form.get("name", "").strip()
    _id = request.form.get("id", "").strip()
    if request.method == "POST":
        result = post(schedule_service_url=schedule_service_url,
                      schedule_cache_key=schedule_cache_key,
                      name=name,
                      _id=_id)
    elif request.method == "DELETE":
        result = delete(schedule_service_url=schedule_service_url,
                        schedule_cache_key=schedule_cache_key,
                        name=name,
                        _id=_id)
    else:
        result = {"message": "Don't support method"}
    return jsonify(result)


@mod_api.route("/check_parse/", methods=["POST"])
@token_required_json
def check_parse(**kwargs):
    """
    解析测试（支持列表页解析、详情页解析、分页解析）
    :return:
    """
    service_url = "http://10.25.171.82:9002"
    path_map = {
        "list": "/test/parse/list",
        "detail": "/test/parse/detail",
        "page": "/test/parse/page"
    }
    # service_url = "http://114.55.110.143:9002"
    check_type = request.form.get("check_type", "check_list_parse")
    arg1 = request.form.get("arg1", "").strip()
    arg2 = request.form.get("arg2", "").strip()
    if not arg1:
        return jsonify(JSON_FIELD_LACK)
    if check_type == "list":
        if arg1 and arg2:
            data = {"url": arg1, "crawler": arg2}
        else:
            data = {"id": ObjectId(arg1)}
    else:
        data = {"url": arg1}
    try:
        url = service_url + path_map.get(check_type, "")
        resp = requests.post(url=url, data=data)
        result = resp.json()
    except Exception as e:
        json_resp = copy.deepcopy(JSON_SERVER_ERROR)
        json_resp["msg"] = str(e)
        return jsonify(json_resp)
    else:
        return jsonify(result)


@mod_api.route("/advertisement/", methods=["POST"])
@token_required_json
def check_advertisement(**kwargs):
    """ 测试、添加广告图"""
    service_url = "http://10.25.171.82:9002/test/advertisement"
    url = request.form.get("url", "").strip()
    referer = request.form.get("referer", "").strip()
    md5 = request.form.get("md5", "").strip()
    if not url:
        return jsonify(JSON_FIELD_LACK)
    try:
        r = requests.post(service_url, data={"url": url, "refer": referer, "md5": md5})
        result = r.json()
    except Exception as e:
        json_resp = copy.deepcopy(JSON_SERVER_ERROR)
        json_resp["msg"] = str(e)
        return jsonify(json_resp)
    else:
        return jsonify(result)


@mod_api.route("/filter_rule/", methods=["POST"])
@token_required_json
def add_filter_rules(**kwargs):
    string = request.form.get("words", "").strip()
    channel = request.form.get("channel", "").strip()
    words = string.split(",")
    if not words or not channel:
        return jsonify(JSON_FIELD_LACK)
    first_channel_id = int(channel)
    result = list()
    for word in words:
        word = word.strip()
        if len(word) < 2:
            continue
        doc = {"word": word, "chid": first_channel_id}
        try:
            mongo_t.db["qidian_filter_rule"].insert(doc)
        except Exception as e:
            logging.warning(e.message)
        else:
            doc["_id"] = str(doc["_id"])
            result.append(doc)
    return jsonify(result)


@mod_api.route("/weibo_comment/", methods=["POST"])
@token_required_json
def weibo_comment(**kwargs):
    def get_news_url(**kw):
        if not by or not content:
            return JSON_FIELD_LACK
        if by == "nid":
            sql = "SELECT url from newslist_v2 where nid=%s;" % content
        elif by == "title":
            sql = "SELECT url from newslist_v2 where title='%s';" % content
        else:
            sql = None
        if sql:
            result = pg_sql(sql)
            url = result[0][0] if result else ""
        else:
            url = content

    by = request.form.get("by", "title")
    content = request.form.get("content", "").strip()
    url = get_news_url(by=by, content=content)
    comment_meta = mongo_p.db.weibo_comment_stat.find_one({"news_url": url})
    if comment_meta:
        return json.dumps(comment_meta, cls=Encoder)
    else:
        return jsonify(JSON_NOT_EXIST)


@mod_api.route("/get_week_stat/", methods=["GET"])
@token_required_json
def get_week_stat(**kwargs):
    result = mongo_t.db.day_stat_form.find({}, {"_id": 0, "data": 1, "day": 1}).sort([("day", -1)]).limit(7)
    result = list(result) if result else []
    result.reverse()
    resp_doc = {"data": result}
    return jsonify(resp_doc)


@mod_api.route("/get_site_data_count/", methods=["GET"])
@token_required_json
def get_site_data_count(**kwargs):
    sid = request.args.get("sid", "").strip()
    today = get_today()
    cols_name = ["v1_news", "v1_joke", "v1_video", "v1_atlas", "v1_picture"]
    count = 0
    for col in cols_name:
        count += mongo_t.db[col].count({"time": {"$gt": today}, "site": sid})
    return jsonify({"sid": "count_" + sid, "count": count})


@mod_api.route("/get_channel_data_count/", methods=["GET"])
@token_required_json
def get_channel_data_count(**kwargs):
    cid = request.args.get("cid", "").strip()
    c_info = mongo_t.db.spider_channels.find_one({"_id": ObjectId(cid)})
    if c_info:
        c_form = c_info.get("form", "news")
    else:
        c_form = "news"
    today = get_today()
    col_name = "v1_" + c_form
    count = mongo_t.db[col_name].count({"time": {"$gt": today}, "channel": str(cid)})
    return jsonify({"cid": "count_" + cid, "count": count})


@mod_api.route("/get_last_db_time/", methods=["GET"])
@token_required_json
def get_last_db_time(**kwargs):
    cid = request.args.get("cid", "").strip()
    c_info = mongo_t.db.spider_channels.find_one({"_id": ObjectId(cid)})
    if c_info:
        c_form = c_info.get("form", "news")
        sid = c_info.get("site", "")
    else:
        c_form = "news"
        sid = ""
    gt_time = datetime.datetime(year=2017, month=1, day=1)
    last_time = mongo_t.db["v1_" + c_form].find({"time": {"$gt": gt_time}, "site": sid, "channel": str(cid)},
                                                {"time": 1}).sort([("time", -1)]).limit(1)
    last_time = list(last_time)
    if last_time:
        last_time = last_time[0]["time"] + datetime.timedelta(hours=8)
        last_time = last_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_time = "0000-00-00 00:00:00"
    return jsonify({"cid": "last_" + cid, "last_time": last_time})


@mod_api.route("/nid_search/", methods=["POST"])
@token_required_json
def nid_search(**kwargs):
    def get_docid(**kw):
        sql_nid_search = "SELECT docid from newslist_v2 where nid=%s;" % nid
        doc_id = pg_sql(sql_nid_search)
        doc_id = doc_id[0][0] if doc_id else ""
        return doc_id

    def is_new(**kw):
        try:
            col, id = doc_id.split("_")
            if col not in ["news", "atlas", "video", "picture", "joke"]:
                check_result = False
            else:
                check_result = True
        except Exception as e:
            check_result = False
        return check_result

    nid_or_url = request.form.get("nid", "").strip()
    nid = re.findall("^\d+$|nid=\d+$", nid_or_url)
    if not nid:
        return jsonify({"msg": "错误，请检查输入字段", "status": 1})
    nid = nid[0].strip("nid=")
    doc_id = get_docid(nid=nid)
    if not doc_id:
        return jsonify({"msg": "查找不到", "status": 1})
    _is_new = is_new(doc_id=doc_id)
    if not _is_new:
        return jsonify({"msg": "不是新版数据", "status": 1})
    col, id = doc_id.split("_")
    result = mongo_t.db["v1_" + col].find_one({"request": id})
    cid = result["channel"]
    sid = result["site"]
    qidian = mongo_t.db.qidian_map.find_one({"channel": cid})
    qd_1_id = qidian["first_cid"] if qidian["first_cid"] else 0
    qd_2_id = qidian["second_cid"] if qidian["second_cid"] else 0
    show_type = qidian["type"]
    sql_cate1 = "select cname from channellist_v2 where id=%s;" % qd_1_id
    sql_cate2 = "select cname from sechannellist_v2 where id=%s;" % qd_2_id
    qd_1 = pg_sql(sql_cate1)
    qd_1 = qd_1[0][0] if qd_1 else u"未设置"
    qd_2 = pg_sql(sql_cate2)
    qd_2 = qd_2[0][0] if qd_2 else u"未设置"
    site = mongo_t.db.spider_sites.find_one({"_id": ObjectId(sid)})
    channel = mongo_t.db.spider_channels.find_one({"_id": ObjectId(cid)})
    config = mongo_t.db.spider_configs.find_one({"channel": cid})
    url = config["request"]["url"]
    params = config["request"]["params"]
    data = dict(
        nid=nid,
        site_name=site["name"],
        site_domain=site["domain"],
        ch_name=channel["name"],
        qd_1=qd_1,
        qd_2=qd_2,
        show_type=show_type,
        mongo_1=channel["category1"] if channel["category1"] else u"未设置",
        mongo_2=channel["category2"] if channel["category2"] else u"未设置",
        ch_url=rebuild_url(url, params)
    )
    return jsonify({"msg": "success", "status": 0, "data": data})
