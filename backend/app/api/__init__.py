"""
API路由模块
"""
from flask import Blueprint

# 创建API蓝图
api_bp = Blueprint('api', __name__)

# 导入所有路由模块
from . import auth
from . import algorithms
from . import datasets
from . import tasks
from . import results