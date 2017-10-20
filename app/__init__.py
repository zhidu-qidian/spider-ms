# coding:utf-8
from flask import Flask
from flask_pymongo import PyMongo
from psycopg2.pool import SimpleConnectionPool

app = Flask(__name__)
app.config.from_object("config")

mongo_p = PyMongo(app)
mongo_t = PyMongo(app, config_prefix="MONGO2")

pg = SimpleConnectionPool(minconn=1, maxconn=5,
                          database=app.config["POSTGRE_DBNAME"],
                          user=app.config["POSTGRE_USER"],
                          password=app.config["POSTGRE_PWD"],
                          host=app.config["POSTGRE_HOST"],
                          port=app.config["POSTGRE_PORT"])

# !!!!!!!下面的/from ... import .../不可提前到文件头!!!!
# 不然会造成循环引用(这是暂时方案)
from app.mod_api.views import mod_api as api_mod
from app.mod_admin.views import mod_admin as admin_mod

app.register_blueprint(api_mod)
app.register_blueprint(admin_mod)
