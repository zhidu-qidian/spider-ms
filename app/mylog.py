# coding:utf-8

"""
日志配置
"""

import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    filename="spider_ms.log",
                    filemode="a+")
