# coding:utf-8
"""
启动脚本
"""

from app import app
from config import DEBUG

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=DEBUG)
