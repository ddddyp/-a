"""
Flask应用工厂模块
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os

# 创建扩展实例
db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name='development'):
    """Flask应用工厂"""
    app = Flask(__name__)
    
    # 配置加载
    if config_name == 'development':
        app.config.update({
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///app.db',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'JWT_SECRET_KEY': 'dev-secret-key-change-in-production',
            'JWT_ACCESS_TOKEN_EXPIRES': False,
            'UPLOAD_FOLDER': os.path.join(os.path.dirname(__file__), '..', 'uploads'),
            'MAX_CONTENT_LENGTH': 100 * 1024 * 1024  # 100MB
        })
    elif config_name == 'production':
        app.config.update({
            'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///app.db'),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', 'change-me-in-production'),
            'JWT_ACCESS_TOKEN_EXPIRES': False,
            'UPLOAD_FOLDER': os.path.join(os.path.dirname(__file__), '..', 'uploads'),
            'MAX_CONTENT_LENGTH': 100 * 1024 * 1024
        })
    
    # 扩展初始化
    db.init_app(app)
    jwt.init_app(app)
    
    # CORS配置 - 支持preflight请求
    CORS(app, 
         origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=True
    )
    
    # 蓝图注册
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 数据库初始化
    with app.app_context():
        db.create_all()
        create_default_user()  # 创建默认管理员
    
    return app


def create_default_user():
    """创建默认管理员用户"""
    from .models.user import User
    
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("默认管理员用户已创建: admin/admin123")