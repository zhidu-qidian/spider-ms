# coding:utf-8

"""一般通用工具"""

import json
import urllib
import urlparse
from datetime import datetime
from datetime import timedelta
from types import StringType
from types import ListType


def url_to_dic(url):
    if isinstance(url, StringType):
        url = url.decode("utf-8")
    fake_url = u"http://xxx.xxx.com?" + url
    parse_result = urlparse.urlparse(fake_url)
    return urlparse.parse_qs(parse_result.query, keep_blank_values=1)


def dic_to_url(dic):
    result = u""
    for k, v in dic.items():
        if not v:
            v = u""
        if isinstance(v, ListType):
            for i in v:
                result += k + u"=" + unicode(i) + u"&"
        else:
            result += k + u"=" + unicode(v) + u"&"

    return result.strip(u"&")


def header_to_str(headers):
    result = []
    for key, value in headers.items():
        item = "%s(:)%s" % (key, value)
        result.append(item)
    return "(#)".join(result)


def str_to_header(text):
    if isinstance(text, StringType):
        text = text.decode("utf-8")
    items = filter(lambda x: x != "", text.strip().split("(#)"))
    result = dict()
    for item in items:
        item = item.split("(:)")
        key = item[0]
        if len(item) > 1:
            value = "".join(item[1:])
        else:
            value = ""
        result[key] = value
    return result


def rebuild_url(url, params):
    for k, v in params.items():
        if isinstance(v, (str, unicode, int)):
            params[k] = [v]
    result = urlparse.urlparse(url)
    query = urlparse.parse_qs(result.query)
    query.update(params)
    for k, v in query.items():
        for i, _v in enumerate(v):
            if isinstance(_v, unicode):
                v[i] = _v.encode("utf-8")
        query[k] = v
    new = list(result)
    new[4] = urllib.urlencode(query, doseq=True)
    return urlparse.urlunparse(tuple(new))


def get_today():
    now = datetime.now()
    today = datetime(year=now.year, month=now.month, day=now.day) - timedelta(hours=8)
    return today


class Encoder(json.JSONEncoder):
    def default(self, obj):
        try:
            obj = json.JSONEncoder.default(self, obj)
        except:
            obj = str(obj)
        return obj
