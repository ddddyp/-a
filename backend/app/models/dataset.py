"""
数据集数据模型
"""
from datetime import datetime
from .. import db


class Dataset(db.Model):
    """数据集模型"""
    __tablename__ = 'datasets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    file_type = db.Column(db.String(10), nullable=False)  # csv, json, xlsx
    file_size = db.Column(db.Integer, nullable=False)  # bytes
    record_count = db.Column(db.Integer, nullable=True)
    column_count = db.Column(db.Integer, nullable=True)
    data_format = db.Column(db.String(50), nullable=True)  # BLTE, Transaction, Generic
    
    # 处理状态
    processed = db.Column(db.Boolean, default=False, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    is_valid = db.Column(db.Boolean, default=True, nullable=False)
    validation_info = db.Column(db.JSON, nullable=True)
    
    # 时间戳
    upload_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # 关系
    tasks = db.relationship('Task', backref='dataset', lazy='dynamic', cascade='all, delete-orphan')
    
    def mark_processed(self):
        """标记为已处理"""
        self.processed = True
        self.processed_at = datetime.utcnow()
        db.session.commit()
    
    def set_validation_info(self, validation_info):
        """设置验证信息"""
        self.validation_info = validation_info
        self.is_valid = validation_info.get('is_valid', True)
        db.session.commit()
    
    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'original_filename': self.original_filename,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'record_count': self.record_count,
            'column_count': self.column_count,
            'data_format': self.data_format,
            'processed': self.processed,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'is_valid': self.is_valid,
            'validation_info': self.validation_info,
            'upload_time': self.upload_time.isoformat(),
            'user_id': self.user_id,
            'task_count': self.tasks.count()
        }
    
    def __repr__(self):
        return f'<Dataset {self.name}>'