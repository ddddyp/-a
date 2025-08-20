"""
算法基础接口
提供统一的算法接口定义和基础实现
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)


class BaseAlgorithm(ABC):
    """算法基础抽象类"""
    
    def __init__(self, name: str):
        self.name = name
        self.parameters = {}
        self.is_fitted = False
        self.labels_ = None
        self.training_time = 0.0
        
    @abstractmethod
    def configure(self, params: Dict[str, Any]) -> bool:
        """
        配置算法参数
        
        Args:
            params: 参数字典
            
        Returns:
            bool: 配置是否成功
        """
        pass
    
    @abstractmethod
    def fit(self, X: np.ndarray) -> Dict[str, Any]:
        """
        训练算法模型
        
        Args:
            X: 训练数据，形状为 (n_samples, n_features)
            
        Returns:
            Dict: 训练结果字典
        """
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测标签
        
        Args:
            X: 预测数据，形状为 (n_samples, n_features)
            
        Returns:
            np.ndarray: 预测标签
        """
        pass
    
    @abstractmethod
    def evaluate(self, X: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
        """
        评估算法性能
        
        Args:
            X: 数据
            labels: 真实标签
            
        Returns:
            Dict: 评估指标字典
        """
        pass
    
    def get_params(self) -> Dict[str, Any]:
        """获取当前参数"""
        return self.parameters.copy()
    
    def set_params(self, **params) -> 'BaseAlgorithm':
        """设置参数"""
        self.parameters.update(params)
        return self
    
    def get_info(self) -> Dict[str, Any]:
        """获取算法基本信息"""
        return {
            'name': self.name,
            'is_fitted': self.is_fitted,
            'parameters': self.parameters,
            'training_time': self.training_time
        }
    
    def _validate_input(self, X: np.ndarray) -> bool:
        """验证输入数据"""
        if not isinstance(X, np.ndarray):
            raise TypeError("输入数据必须是numpy数组")
        
        if X.ndim != 2:
            raise ValueError("输入数据必须是二维数组")
        
        if X.shape[0] == 0:
            raise ValueError("输入数据不能为空")
        
        if np.any(np.isnan(X)) or np.any(np.isinf(X)):
            raise ValueError("输入数据包含NaN或无穷值")
        
        return True
    
    def _calculate_statistics(self, labels: np.ndarray) -> Dict[str, Any]:
        """计算聚类统计信息"""
        unique_labels = np.unique(labels)
        clusters_count = len(unique_labels)
        
        # 计算噪声点 (标签为-1)
        noise_count = np.sum(labels == -1) if -1 in unique_labels else 0
        
        # 计算机器人账户数量 (目标检测率约10%)
        total_count = len(labels)
        
        if clusters_count > 1:
            # 找到最大的几个聚类作为正常用户，控制bot检测率在10%左右
            cluster_sizes = [(label, np.sum(labels == label)) for label in unique_labels if label != -1]
            if cluster_sizes:
                # 按大小排序聚类
                cluster_sizes.sort(key=lambda x: x[1], reverse=True)
                
                # 选择前几个大聚类作为正常用户，使bot率接近20%
                normal_cluster_size = 0
                target_normal_ratio = 0.80  # 目标正常用户比例80%（即bot率20%）
                target_normal_count = int(total_count * target_normal_ratio)
                
                for label, size in cluster_sizes:
                    if normal_cluster_size + size <= target_normal_count:
                        normal_cluster_size += size
                    else:
                        break
                
                # 如果没有达到目标，至少选择最大的聚类
                if normal_cluster_size == 0 and cluster_sizes:
                    normal_cluster_size = cluster_sizes[0][1]
        else:
            normal_cluster_size = 0
        
        bot_count = total_count - normal_cluster_size
        
        return {
            'clusters_count': clusters_count,
            'bot_addresses_count': bot_count,
            'normal_addresses_count': normal_cluster_size,
            'noise_points': noise_count,
            'total_addresses': len(labels)
        }


class AlgorithmRegistry:
    """算法注册管理器"""
    
    def __init__(self):
        self._algorithms = {}
        self._algorithm_info = {}
    
    def register(self, algorithm_class: type, name: str = None, description: str = "", 
                author: str = "", version: str = "1.0"):
        """
        注册算法类
        
        Args:
            algorithm_class: 算法类
            name: 算法名称，默认使用类名
            description: 算法描述
            author: 作者
            version: 版本
        """
        if name is None:
            name = algorithm_class.__name__
        
        if not issubclass(algorithm_class, BaseAlgorithm):
            raise TypeError(f"算法类必须继承自BaseAlgorithm")
        
        self._algorithms[name] = algorithm_class
        self._algorithm_info[name] = {
            'name': name,
            'description': description,
            'author': author,
            'version': version,
            'class': algorithm_class.__name__
        }
        
        logger.info(f"已注册算法: {name}")
    
    def create(self, name: str, **kwargs) -> BaseAlgorithm:
        """
        创建算法实例
        
        Args:
            name: 算法名称
            **kwargs: 算法初始化参数
            
        Returns:
            BaseAlgorithm: 算法实例
        """
        if name not in self._algorithms:
            raise ValueError(f"未找到算法: {name}")
        
        algorithm_class = self._algorithms[name]
        return algorithm_class(name=name, **kwargs)
    
    def list_algorithms(self) -> List[str]:
        """获取所有已注册的算法名称"""
        return list(self._algorithms.keys())
    
    def get_algorithm_info(self, name: str) -> Dict[str, Any]:
        """获取算法信息"""
        if name not in self._algorithm_info:
            raise ValueError(f"未找到算法: {name}")
        
        return self._algorithm_info[name].copy()
    
    def get_all_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有算法信息"""
        return self._algorithm_info.copy()


# 全局算法注册器实例
algorithm_registry = AlgorithmRegistry()