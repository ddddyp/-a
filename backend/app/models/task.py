"""
任务数据模型
"""
from datetime import datetime
from .. import db


class Task(db.Model):
    """任务模型"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    algorithm_name = db.Column(db.String(100), nullable=False, index=True)
    parameters = db.Column(db.JSON, nullable=True)
    
    # 任务状态
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    # pending, running, completed, failed, cancelled
    progress = db.Column(db.Integer, default=0, nullable=False)  # 0-100
    current_stage = db.Column(db.String(100), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # 性能指标
    processing_time = db.Column(db.Float, nullable=True)  # 处理时间(秒)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False, index=True)
    
    # 关系
    results = db.relationship('Result', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    def update_progress(self, progress, stage=None):
        """更新任务进度"""
        self.progress = progress
        if stage:
            self.current_stage = stage
        db.session.commit()
    
    def mark_running(self):
        """标记任务开始运行"""
        self.status = 'running'
        self.started_at = datetime.utcnow()
        self.progress = 0
        db.session.commit()
    
    def mark_completed(self, processing_time=None):
        """标记任务完成"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.progress = 100
        self.current_stage = '分析完成'
        if processing_time:
            self.processing_time = processing_time
        db.session.commit()
    
    def mark_failed(self, error_message):
        """标记任务失败"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def mark_cancelled(self):
        """标记任务取消"""
        self.status = 'cancelled'
        self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'algorithm_name': self.algorithm_name,
            'parameters': self.parameters,
            'status': self.status,
            'progress': self.progress,
            'current_stage': self.current_stage,
            'error_message': self.error_message,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'user_id': self.user_id,
            'dataset_id': self.dataset_id,
            'result_count': self.results.count()
        }
    
    def __repr__(self):
        return f'<Task {self.name} - {self.status}>'