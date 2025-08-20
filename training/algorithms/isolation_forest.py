"""
IsolationForest算法实现
基于隔离的异常检测算法，专门用于识别异常行为模式
"""
import numpy as np
import time
from typing import Dict, Any
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from collections import Counter

from .base import BaseAlgorithm, algorithm_registry


class IsolationForestAlgorithm(BaseAlgorithm):
    """IsolationForest异常检测算法"""
    
    def __init__(self, name: str = "IsolationForest"):
        super().__init__(name)
        self.model = None
        self.decision_scores = None
        self.anomaly_threshold = None
        
        # 默认参数
        self.parameters = {
            'n_estimators': 'auto',  # 自动选择或指定数值
            'contamination': 'auto',  # 自动选择或指定数值
            'max_samples': 'auto',
            'max_features': 1.0,
            'bootstrap': False,
            'n_jobs': -1,
            'random_state': 42,
            'verbose': 0
        }
    
    def configure(self, params: Dict[str, Any]) -> bool:
        """配置IsolationForest参数"""
        try:
            valid_params = ['n_estimators', 'contamination', 'max_samples', 'max_features', 
                          'bootstrap', 'n_jobs', 'random_state', 'verbose']
            for key, value in params.items():
                if key in valid_params:
                    self.parameters[key] = value
                else:
                    print(f"警告: 无效参数 {key}")
            return True
        except Exception as e:
            print(f"参数配置失败: {e}")
            return False
    
    def _hyperparameter_optimization(self, X: np.ndarray) -> Dict[str, Any]:
        """
        基于数据特征自适应调整超参数
        
        Args:
            X: 输入数据
            
        Returns:
            Dict: 优化后的参数
        """
        n_samples, n_features = X.shape
        
        # 自适应contamination（目标检测率20%，保持高轮廓系数）
        if self.parameters['contamination'] == 'auto':
            # 调整contamination到20%目标检测率，同时优化轮廓系数
            base_contamination = 0.20  # 目标检测率20%
            
            # 基于数据集大小的优化调整，平衡检测率和轮廓系数
            if n_samples <= 1000:
                # 800样本：提高到约20%
                contamination = base_contamination * 0.9  # 0.18
            elif n_samples <= 10000:
                # 5000样本：提高到约20%
                contamination = base_contamination * 0.85  # 0.17
            else:
                # 20000样本：提高到约20%
                contamination = base_contamination * 0.8  # 0.16
            
            # 确保在合理范围内，扩大范围以支持更高检测率
            contamination = max(0.10, min(0.25, contamination))
        else:
            contamination = self.parameters['contamination']
        
        # 自适应n_estimators（保持高轮廓系数的同时支持20%检测率）
        if self.parameters['n_estimators'] == 'auto':
            # 进一步增加树的数量以保持高轮廓系数，补偿提高检测率的影响
            if n_samples < 1000:
                n_estimators = 300  # 进一步增加到300
            elif n_samples < 10000:
                n_estimators = 400  # 进一步增加到400
            else:
                n_estimators = 600  # 进一步增加到600
        else:
            n_estimators = self.parameters['n_estimators']
        
        # 自适应max_samples
        if self.parameters['max_samples'] == 'auto':
            max_samples = min(256, n_samples)
        else:
            max_samples = self.parameters['max_samples']
        
        optimized_params = {
            'contamination': contamination,
            'n_estimators': n_estimators,
            'max_samples': max_samples,
            'max_features': self.parameters['max_features'],
            'bootstrap': self.parameters['bootstrap'],
            'n_jobs': self.parameters['n_jobs'],
            'random_state': self.parameters['random_state'],
            'verbose': self.parameters['verbose']
        }
        
        return optimized_params
    
    def _convert_to_binary_labels(self, anomaly_labels: np.ndarray) -> np.ndarray:
        """
        将异常检测结果转换为二分类标签
        
        Args:
            anomaly_labels: IsolationForest的输出 (1为正常，-1为异常)
            
        Returns:
            np.ndarray: 转换后的标签 (0为正常，1为异常)
        """
        # 将-1(异常)转换为1，1(正常)转换为0
        binary_labels = np.where(anomaly_labels == -1, 1, 0)
        return binary_labels
    
    def fit(self, X: np.ndarray) -> Dict[str, Any]:
        """训练IsolationForest模型"""
        try:
            # 验证输入
            self._validate_input(X)
            
            start_time = time.time()
            
            # 参数优化
            optimized_params = self._hyperparameter_optimization(X)
            
            # 创建和训练模型
            self.model = IsolationForest(**optimized_params)
            
            # 执行异常检测
            anomaly_labels = self.model.fit_predict(X)  # 1为正常，-1为异常
            decision_scores = self.model.decision_function(X)  # 异常分数
            
            # 转换为二分类标签用于聚类评估
            binary_labels = self._convert_to_binary_labels(anomaly_labels)
            
            self.labels_ = binary_labels
            self.decision_scores = decision_scores
            self.is_fitted = True
            
            self.training_time = time.time() - start_time
            
            # 计算统计信息
            unique_labels = np.unique(binary_labels)
            clusters_count = len(unique_labels)
            
            # 统计正常和异常数量
            normal_count = np.sum(binary_labels == 0)  # 正常用户
            anomaly_count = np.sum(binary_labels == 1)  # 异常用户(机器人)
            
            # 计算轮廓系数
            silhouette = 0.0
            if clusters_count > 1:
                try:
                    silhouette = silhouette_score(X, binary_labels)
                except:
                    silhouette = 0.0
            
            # 聚类详细统计
            cluster_stats = {
                '正常用户': {
                    'size': normal_count,
                    'percentage': (normal_count / len(binary_labels)) * 100
                },
                '异常用户(机器人)': {
                    'size': anomaly_count,
                    'percentage': (anomaly_count / len(binary_labels)) * 100
                }
            }
            
            # 异常分数统计
            anomaly_scores_stats = {
                'mean_score': float(np.mean(decision_scores)),
                'std_score': float(np.std(decision_scores)),
                'min_score': float(np.min(decision_scores)),
                'max_score': float(np.max(decision_scores)),
                'anomaly_threshold': float(np.percentile(decision_scores, 
                                                       (1 - optimized_params['contamination']) * 100))
            }
            
            result = {
                'algorithm_name': self.name,
                'labels': binary_labels.tolist(),
                'clusters_count': clusters_count,
                'bot_addresses_count': anomaly_count,
                'normal_addresses_count': normal_count,
                'noise_points': 0,  # IsolationForest没有噪声点概念
                'silhouette_score': silhouette,
                'cluster_stats': cluster_stats,
                'anomaly_scores': decision_scores.tolist(),
                'anomaly_scores_stats': anomaly_scores_stats,
                'parameters_used': optimized_params,
                'training_time': self.training_time
            }
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"IsolationForest训练失败: {str(e)}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测新数据的异常标签"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练，请先调用fit方法")
        
        try:
            self._validate_input(X)
            
            # 预测异常标签
            anomaly_labels = self.model.predict(X)
            
            # 转换为二分类标签
            binary_labels = self._convert_to_binary_labels(anomaly_labels)
            
            return binary_labels
            
        except Exception as e:
            raise RuntimeError(f"预测失败: {str(e)}")
    
    def get_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """获取异常分数"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练")
        
        return self.model.decision_function(X)
    
    def evaluate(self, X: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
        """评估IsolationForest性能"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练")
        
        try:
            metrics = {}
            
            # 轮廓系数
            if len(set(labels)) > 1:
                metrics['silhouette_score'] = silhouette_score(X, labels)
            else:
                metrics['silhouette_score'] = 0.0
            
            # 异常检测率
            anomaly_rate = np.sum(labels == 1) / len(labels)
            metrics['anomaly_rate'] = anomaly_rate
            
            # 聚类数量
            metrics['n_clusters'] = len(set(labels))
            
            # 异常分数统计
            if self.decision_scores is not None:
                metrics['mean_anomaly_score'] = np.mean(self.decision_scores)
                metrics['std_anomaly_score'] = np.std(self.decision_scores)
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}


# 注册算法
algorithm_registry.register(
    IsolationForestAlgorithm,
    name="IsolationForest",
    description="基于隔离的异常检测算法，通过隔离异常点来识别机器人行为",
    author="区块链",
    version="2.0"
)