"""
用户数据模型
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # 关系定义
    datasets = db.relationship('Dataset', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """密码加密存储"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """密码验证"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'dataset_count': self.datasets.count(),
            'task_count': self.tasks.count()
        }
    
    def __repr__(self):
        return f'<User {self.username}>'