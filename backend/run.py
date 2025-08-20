"""
Flask应用启动文件
"""
import os
import sys

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app import create_app

# 创建Flask应用实例
app = create_app()

if __name__ == '__main__':
    # 开发模式运行
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )