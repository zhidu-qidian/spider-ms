# coding:utf-8

"""
配置文件，涉及数据库和Token密钥
"""

import os

DEBUG = True

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if DEBUG:
    MONGO_HOST = "公网IP"
else:
    MONGO_HOST = "内网IP"
MONGO_PORT = 27017
MONGO_DBNAME = "patianxia"
MONGO_USERNAME = ""
MONGO_PASSWORD = ""

MONGO2_HOST = MONGO_HOST
MONGO2_PORT = MONGO_PORT
MONGO2_DBNAME = ""
MONGO2_USERNAME = ""
MONGO2_PASSWORD = ""

if DEBUG:
    POSTGRE_HOST = "公网IP"
else:
    POSTGRE_HOST = "内网IP"
POSTGRE_USER = ""
POSTGRE_PWD = ""
POSTGRE_DBNAME = ""
POSTGRE_PORT = 5432

REDIS_URL = "redis://内网IP:6379"
REDIS_MAX_CONNECTIONS = 1

SECRET_KEY = "Qidian@LieYing@Zhidu"
