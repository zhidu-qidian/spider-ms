# coding:utf-8

"""oss上传工具函数"""

import json
import uuid
import oss2
from app.mylog import logging

access_key_id = ""
access_key_secret = ""
auth = oss2.Auth(access_key_id, access_key_secret)
region = "https://oss-cn-hangzhou.aliyuncs.com"
name = "bdp-images"
bucket = oss2.Bucket(auth, region, name)


def is_allowed(file_mine):
    """检查上传文件是否是允许的类型"""
    return file_mine == "image/jpeg"


def upload_file_to_oss(file_mime, data):
    """上传图片到oss"""
    if not is_allowed(file_mime):
        return False
    target_name = str(uuid.uuid1().hex) + ".jpg"
    try:
        respond = bucket.put_object(target_name, data)
    except Exception as e:
        logging.warning(e)
        logging.warning("upload image exception")
        return False
    if respond.status != 200:
        logging.info("upload image to oss error: %s" % respond.status)
        return False
    pic_url = 'https://oss-cn-hangzhou.aliyuncs.com/bdp-images/' + target_name
    return pic_url
