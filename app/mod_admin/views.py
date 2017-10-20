# coding:utf-8

"""
和html界面相关的视图：
    登陆登出页面视图
    主界面视图
    网站添加视图
    网站搜索视图
    网站修改视图
    频道添加视图
    频道搜索视图
    频道修改视图
"""
import datetime
import requests
from flask import Blueprint
from flask import request
from flask import render_template
from flask import redirect
from flask import make_response
from bson.objectid import ObjectId
from redis import from_url
from app.auth import token_required_html
from app.auth import User
from app.utils.general import dic_to_url
from app.utils.general import header_to_str
from app.utils.general import rebuild_url
from app.utils.general import get_today
from app.utils.db import pg_sql
from config import REDIS_URL, REDIS_MAX_CONNECTIONS
from config import DEBUG
from app import mongo_t
from app import pg

mod_admin = Blueprint('admin', __name__,
                      url_prefix='/',
                      template_folder="templates",
                      static_folder="static")


@mod_admin.route("/", methods=["POST", "GET"])
@token_required_html
def index(*args, **kwargs):
    token = kwargs.get("token")
    today = get_today()
    names = ["v1_news", "v1_joke", "v1_video", "v1_atlas", "v1_picture"]
    result = list()
    for name in names:
        count = mongo_t.db[name].count({"time": {"$gt": today}})
        _name = name.split("_")[-1]
        result.append({"name": _name, "count": count})
    sites = list(mongo_t.db.spider_sites.find({}, {"_id": 1, "name": 1, "domain": 1}))
    resp = make_response(render_template("admin/index.html",
                                         data=result,
                                         sites=sites))
    if token:
        resp.set_cookie("token", token)
    return resp


@mod_admin.route("stat_comment/", methods=["POST", "GET"])
@token_required_html
def stat_comment(**kwargs):
    return render_template("admin/stat_comment.html")


@mod_admin.route("spider_monitor/", methods=["POST", "GET"])
@token_required_html
def spider_monitor(**kwargs):
    status = request.args.get("status", "")
    types = request.args.get("types", "")
    condition = {}
    if status != "":
        condition["procedure"] = int(status)
    if types != "":
        condition["form"] = types
    projection = {"_id": 1, "channel": 1, "time": 1, "form": 1}
    result = mongo_t.db.v1_request.find(condition, projection).sort([("_id", -1)]).limit(10)
    return render_template("admin/spider_monitor.html",
                           result=list(result))


@mod_admin.route("db_query/", methods=["POST", "GET"])
@token_required_html
def db_query(**kwargs):
    col_list = mongo_t.db.collection_names()
    col_list = sorted(col_list)
    return render_template("admin/db_query.html",
                           collections=col_list)


@mod_admin.route("login/", methods=["POST", "GET"])
def login(**kwargs):
    if User.is_login():
        return redirect("/")
    return render_template("admin/login.html")


@mod_admin.route("logout/", methods=["POST", "GET"])
@token_required_html
def logout(**kwargs):
    resp = make_response(render_template("admin/login.html"))
    resp.set_cookie("token", "")
    return resp


@mod_admin.route("add_site/", methods=["POST", "GET"])
@token_required_html
def add_site(**kwargs):
    return render_template("admin/add_site.html")


@mod_admin.route("add_channel/", methods=["POST", "GET"])
@token_required_html
def add_channel(**kwargs):
    domain = request.args.get("domain", "").strip()
    data_forms = list(mongo_t.db.data_forms.find({}))
    cate1_items = list(mongo_t.db.data_category_one.find(
        {}, {"name": 1, "_id": 0}))
    sql = "select id,cname from channellist_v2 order by id desc;"
    result = pg_sql(sql)
    qd_cate1 = list()
    for item in result:
        one_cate = {
            "id": item[0],
            "name": item[1].decode("utf-8")
        }
        qd_cate1.append(one_cate)
    return render_template("admin/add_channel.html",
                           domain=domain,
                           cate1_items=cate1_items,
                           data_forms=data_forms,
                           qd_cate1=qd_cate1)


@mod_admin.route("search_site/", methods=["GET"])
@token_required_html
def search_site(**kwargs):
    by = request.args.get("by", "domain")
    content = request.args.get("content", "").strip()
    page = int(request.args.get("page", 1))
    num_per_page = 10
    condition = {}
    if content:
        if by == "domain":
            condition["domain"] = content
        elif by == "id":
            condition["_id"] = ObjectId(content)
        elif by == "name":
            condition["name"] = content
        else:
            condition["domain"] = content

    site_count = int(mongo_t.db.spider_sites.count(condition))
    pages = (site_count + num_per_page - 1) / num_per_page
    sites = list(
        mongo_t.db.spider_sites.find(condition).sort([("_id", -1)]).skip(
            num_per_page * (page - 1)).limit(num_per_page))
    today = get_today()
    cols_name = ["v1_news", "v1_joke", "v1_video", "v1_atlas", "v1_picture"]
    for num, site in enumerate(sites):
        sid = str(site["_id"])
        day_count = 0
        for col in cols_name:
            day_count += mongo_t.db[col].count({"time": {"$gt": today}, "site": sid})
        sites[num]["day_count"] = day_count
    current = page
    pagination = {}
    pagination["by"] = by
    pagination["content"] = content
    pagination["total"] = pages
    pagination["current"] = current
    pagination["pre"] = current - 1
    pagination["next"] = current + 1

    return render_template("admin/search_site.html",
                           sites=sites, pagination=pagination)


@mod_admin.route("search_channel/", methods=["POST", "GET"])
@token_required_html
def search_channel(**kwargs):
    def get_next_time(ids):
        sch_url = "http://10.25.60.218:9000/tasks"
        resp_doc = requests.get(sch_url, data={"id": ids}).json()
        jobs = dict()
        for i in resp_doc["jobs"]:
            key = i["id"]
            value = i["next"]
            jobs[key] = value
        return jobs

    def get_condition(**kw):
        condition = dict()
        if content:
            if by == "site_domain":
                site = list(mongo_t.db.spider_sites.find(
                    {"domain": content}, {"_id": 1}))
                if site:
                    site_id = site[0]["_id"]
                else:
                    site_id = 0
                condition["site"] = str(site_id)
            elif by == "site_name":
                site = list(mongo_t.db.spider_sites.find(
                    {"name": content}, {"_id": 1}))
                if site:
                    site_id = site[0]["_id"]
                else:
                    site_id = 0
                condition["site"] = str(site_id)
            elif by == "site_id":
                condition["site"] = content
            elif by == "channel_id":
                condition["_id"] = ObjectId(content)
            elif by == "channel_name":
                condition["name"] = content
            else:
                site = list(mongo_t.db.spider_sites.find(
                    {"domain": content}, {"_id": 1}))
                if site:
                    site_id = site[0]["_id"]
                else:
                    site_id = 0
                condition["site"] = site_id
        return condition

    def get_channel_detail(**kw):
        _channels = channels[:]
        if DEBUG:
            jobs = list()
        else:
            jobs = get_next_time(ids)
        for num, _channel in enumerate(_channels):
            cid = _channel["_id"]
            sid = _channel["site"]
            c_form = _channel["form"]
            we_id = _channel["meta"].get("name", "")
            if str(sid) == "57bab42eda083a1c19957b1f":  # wechat site-id
                wechat_search = u'<a href="http://weixin.sogou.com/weixin?type=1&query={}&ie=utf8&_sug_=n&_sug_type_=" target="_blank">点击查看</a>'.format(
                    we_id)
            else:
                wechat_search = "N/A"
            channels[num]["wechat_search"] = wechat_search
            site = list(mongo_t.db.spider_sites.find({"_id": ObjectId(_channel["site"])},
                                                     {"_id": 0, "name": 1}))[0]
            channels[num]["site_name"] = site["name"]
            try:
                conf_id = ObjectId(_channel["config"][0])
                conf = list(mongo_t.db.spider_configs.find(
                    {"_id": conf_id}))
            except:
                conf = None
            if conf:
                import json
                rules = conf[0].get("rules", [])
                channels[num]["rules"] = " # ".join(rules)
                channels[num]["crawler"] = conf[0].get("crawler", "")
                req = conf[0].get("request", {})
                url = req.get("url", "")
                params = req.get("params", {})
                url = rebuild_url(url, params)
                channels[num]["url"] = url
                channels[num]["request"] = json.dumps(req).decode("utf-8").encode("utf-8")
            else:
                channels[num]["rules"] = ""
                channels[num]["request"] = "{}"
            if DEBUG:
                channels[num]["next_time"] = u"DEBUG模式无数据"
            else:
                channels[num]["next_time"] = jobs.get(_channel["config"][0], "0000-00-00 00:00:00")
        return channels

    by = request.args.get("by", "site_domain").strip()
    content = request.args.get("content", "").strip()
    page = int(request.args.get("page", 1))
    num_per_page = 10
    condition = get_condition(by=by, content=content)
    channel_count = int(mongo_t.db.spider_channels.count(condition))
    pages = (channel_count + num_per_page - 1) / num_per_page
    channels = list(mongo_t.db.spider_channels.find(condition).sort([("_id", -1)]).skip(
        num_per_page * (page - 1)).limit(num_per_page))
    ids = [channel["config"][0] for channel in channels]
    channels = get_channel_detail(channels=channels, ids=ids)
    current = page
    pagination = {}
    pagination["by"] = by
    pagination["content"] = content
    pagination["total"] = pages
    pagination["current"] = current
    pagination["pre"] = current - 1
    pagination["next"] = current + 1
    return render_template("admin/search_channel.html",
                           channels=channels,
                           pagination=pagination,
                           by=by,
                           condition_content=content)


@mod_admin.route("modify_site/", methods=["GET"])
@token_required_html
def modify_site(**kwargs):
    domain = request.args.get("domain")
    site = list(mongo_t.db.spider_sites.find({"domain": domain}))[0]
    return render_template("admin/modify_site.html", site=site)


@mod_admin.route("modify_channel/", methods=["GET"])
@token_required_html
def modify_channel(**kwargs):
    cid = request.args.get("id")
    channel = list(mongo_t.db.spider_channels.find(
        {"_id": ObjectId(cid)}))[0]
    meta = channel["meta"]
    channel["author"] = meta.get("name", "")
    channel["biz"] = meta.get("_biz", "")
    channel["certification"] = meta.get("certification", "")
    data_forms = list(mongo_t.db.data_forms.find({}))
    cate1_items = list(mongo_t.db.data_category_one.find(
        {}, {"name": 1, "_id": 0}))
    try:
        conf_id = ObjectId(channel["config"][0])
        conf = mongo_t.db.spider_configs.find_one(
            {"_id": conf_id})
    except:
        conf = None
    if conf:
        rules = conf.get("rules", [])
        channel["rules"] = " # ".join(rules)
        headers = conf["request"].get("headers", {})
        channel["headers"] = header_to_str(headers)
        params = conf["request"].get("params", {})
        channel["params"] = dic_to_url(params)
        url = conf["request"].get("url", "")
        channel["url"] = url
        crawler = conf.get("crawler", "")
        channel["crawler"] = crawler
        method = conf["request"].get("method", "")
        channel["method"] = method
        ua_type = conf["request"].get("user_agent_type", "pc")
        channel["ua_type"] = ua_type

    else:
        channel["rules"] = ""
        channel["headers"] = "{}"
    types = [
        {"key": "general", "name": u"一般类型"},
        {"key": "big", "name": u"大图类型"},
        {"key": "hot", "name": u"热点类型"}
    ]
    map_info = mongo_t.db.qidian_map.find_one({"channel": str(cid)})
    channel["target_type"] = map_info["type"].split("#")
    channel["types"] = types
    channel["qd_cate1"] = str(map_info["first_cid"] if map_info["first_cid"] else 0)
    channel["qd_cate2"] = dict()
    channel["qd_cate2"]["id"] = str(map_info["second_cid"] if map_info["second_cid"] else 0)
    sql_cate1_list = "select id,cname from channellist_v2 order by id desc;"
    sql_cate2 = "select cname from sechannellist_v2 where id=%s;" % channel["qd_cate2"]["id"]
    result = pg_sql(sql_cate1_list)
    cate2_result = pg_sql(sql_cate2)
    channel["qd_cate2"]["name"] = cate2_result[0][0] if cate2_result else ""
    channel["qd_cate2"]["name"] = channel["qd_cate2"]["name"].decode("utf-8")
    qd_cate1 = list()
    for item in result:
        one_cate = {
            "id": str(item[0]),
            "name": item[1].decode("utf-8")
        }
        qd_cate1.append(one_cate)
    site = mongo_t.db.spider_sites.find_one({"_id": ObjectId(channel["site"])},
                                            {"_id": 0, "name": 1})

    channel["site_name"] = site["name"]
    return render_template("admin/modify_channel.html",
                           data_forms=data_forms,
                           cate1_items=cate1_items,
                           channel=channel,
                           qd_cate1=qd_cate1)


@mod_admin.route("check_parse/", methods=["GET"])
@token_required_html
def check_parse(**kwargs):
    return render_template("admin/check_parse.html")


@mod_admin.route("weibo_comment/", methods=["GET"])
@token_required_html
def weibo_comment(**kwargs):
    return render_template("admin/weibo_comment.html")


@mod_admin.route("advertisement/", methods=["GET"])
@token_required_html
def advertisement(**kwargs):
    return render_template("admin/advertisement.html")


@mod_admin.route("filter_rule/", methods=["GET"])
@token_required_html
def filter_rule(**kwargs):
    return render_template("admin/filter_rule.html")


@mod_admin.route("redis_info/", methods=["GET"])
@token_required_html
def redis_info(**kwargs):
    db = int(request.args.get("redis_db", 2))
    max_len = 1
    result = []
    redis = from_url(REDIS_URL, db=db, max_connections=REDIS_MAX_CONNECTIONS)
    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    keys = redis.keys("*")
    for num, key in enumerate(keys):
        type = redis.type(key)
        if type == "string":
            key_len = redis.strlen(key)
        elif type == "hash":
            key_len = redis.hlen(key)
        elif type == "set":
            key_len = redis.scard(key)
        elif type == "list":
            key_len = redis.llen(key)

        if key_len > max_len:
            one_item = {
                "db": db,
                "key": key,
                "length": key_len,
                "time": time_now}
            result.append(one_item)
        result = sorted(result, key=lambda x: x.get("length", 0), reverse=True)
    return render_template("admin/redis_info.html", result=result)


@mod_admin.route("except_report/", methods=["GET"])
@token_required_html
def except_report(**kwargs):
    condition = {}
    default_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    date = request.args.get("date", default_date)
    condition["date"] = date
    type = request.args.get("type")
    if type and type in ["list", "detail", "unknown"]:
        condition["type"] = type + "-error"
    result = list(mongo_t.db.exception_report.find(condition))
    total_count = len(result)
    for num, item in enumerate(result):
        ex_info = str(item["ex_info"])
        result[num]["ex_info"] = ex_info.decode("unicode-escape")
    return render_template("admin/except_report.html",
                           result=result,
                           total_count=total_count)
