"""
分析结果数据模型
"""
from datetime import datetime
from .. import db


class Result(db.Model):
    """分析结果模型"""
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    algorithm_name = db.Column(db.String(100), nullable=False, index=True)
    
    # 核心指标
    clusters_count = db.Column(db.Integer, nullable=False)
    bot_addresses_count = db.Column(db.Integer, nullable=False)
    bot_addresses_pct = db.Column(db.Float, nullable=False)
    normal_addresses_count = db.Column(db.Integer, nullable=False)
    normal_addresses_pct = db.Column(db.Float, nullable=False)
    noise_points = db.Column(db.Integer, default=0, nullable=False)
    noise_points_pct = db.Column(db.Float, default=0, nullable=False)
    
    # 评估指标
    silhouette_score = db.Column(db.Float, nullable=True)
    detection_accuracy = db.Column(db.Float, default=0, nullable=False)
    
    # 详细结果 (JSON存储)
    cluster_labels = db.Column(db.JSON, nullable=True)
    cluster_stats = db.Column(db.JSON, nullable=True)
    evaluation_metrics = db.Column(db.JSON, nullable=True)
    
    # 元数据
    total_addresses = db.Column(db.Integer, nullable=False)
    feature_count = db.Column(db.Integer, nullable=False)
    data_format = db.Column(db.String(50), nullable=False)
    processing_time = db.Column(db.Float, nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 外键
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False, index=True)
    
    @property
    def quality_level(self):
        """根据轮廓系数返回质量等级"""
        if not self.silhouette_score:
            return '未知'
        
        score = self.silhouette_score
        if score > 0.7:
            return '优秀'
        elif score > 0.3:
            return '良好'
        elif score > 0.1:
            return '一般'
        else:
            return '较差'
    
    @property
    def detection_rate_level(self):
        """根据检测率返回检测水平"""
        rate = self.bot_addresses_pct
        if 5 <= rate <= 15:
            return '正常'
        elif 2 <= rate <= 20:
            return '警告'
        else:
            return '异常'
    
    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'algorithm_name': self.algorithm_name,
            'clusters_count': self.clusters_count,
            'bot_addresses_count': self.bot_addresses_count,
            'bot_addresses_pct': self.bot_addresses_pct,
            'normal_addresses_count': self.normal_addresses_count,
            'normal_addresses_pct': self.normal_addresses_pct,
            'noise_points': self.noise_points,
            'noise_points_pct': self.noise_points_pct,
            'silhouette_score': self.silhouette_score,
            'detection_accuracy': self.detection_accuracy,
            'cluster_labels': self.cluster_labels,
            'cluster_stats': self.cluster_stats,
            'evaluation_metrics': self.evaluation_metrics,
            'total_addresses': self.total_addresses,
            'feature_count': self.feature_count,
            'data_format': self.data_format,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat(),
            'task_id': self.task_id,
            'quality_level': self.quality_level,
            'detection_rate_level': self.detection_rate_level
        }
    
    def to_summary_dict(self):
        """序列化为摘要字典（不包含大数据字段）"""
        summary = self.to_dict()
        # 移除大数据字段以节省传输
        summary.pop('cluster_labels', None)
        summary.pop('evaluation_metrics', None)
        return summary
    
    def __repr__(self):
        return f'<Result {self.algorithm_name} - {self.silhouette_score:.3f}>'