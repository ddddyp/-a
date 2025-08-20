"""
算法服务 - 核心业务逻辑层
提供算法执行、结果处理、性能监控等功能
"""
import os
import time
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from sklearn.metrics import silhouette_score

import sys
import os
# Add parent directory to path to access training module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from training.algorithms.base import algorithm_registry
from training.features.feature_extractor import OptimizedFeatureExtractor


class AlgorithmService:
    """算法服务 - 管理算法执行和结果处理"""
    
    def __init__(self, use_optimized_features: bool = True):
        """
        初始化算法服务
        
        Args:
            use_optimized_features: 是否使用优化的特征提取器
        """
        if use_optimized_features:
            self.feature_extractor = OptimizedFeatureExtractor()
        else:
            from ...training.features.feature_extractor import FeatureExtractor
            self.feature_extractor = FeatureExtractor()
        
        self.supported_algorithms = ['DBSCAN', 'IsolationForest', 'KmeansPlus']
        
    def get_available_algorithms(self) -> Dict[str, Any]:
        """
        获取所有可用算法信息
        
        Returns:
            Dict: 算法信息字典
        """
        algorithms_info = {}
        
        for algorithm_name in algorithm_registry.list_algorithms():
            try:
                info = algorithm_registry.get_algorithm_info(algorithm_name)
                algorithms_info[algorithm_name] = info
            except Exception as e:
                algorithms_info[algorithm_name] = {
                    'error': str(e),
                    'status': 'unavailable'
                }
        
        return algorithms_info
    
    def get_algorithm_info(self, algorithm_name: str) -> Dict[str, Any]:
        """
        获取指定算法的详细信息
        
        Args:
            algorithm_name: 算法名称
            
        Returns:
            Dict: 算法详细信息
            
        Raises:
            ValueError: 算法不存在
        """
        if algorithm_name not in algorithm_registry.list_algorithms():
            raise ValueError(f"算法 '{algorithm_name}' 不存在")
        
        info = algorithm_registry.get_algorithm_info(algorithm_name)
        
        # 获取默认参数
        try:
            algorithm = algorithm_registry.create(algorithm_name)
            info['default_parameters'] = algorithm.get_params()
        except Exception:
            info['default_parameters'] = {}
        
        return info
    
    def validate_algorithm_parameters(self, algorithm_name: str, 
                                    parameters: Dict[str, Any]) -> bool:
        """
        验证算法参数有效性
        
        Args:
            algorithm_name: 算法名称
            parameters: 参数字典
            
        Returns:
            bool: 参数是否有效
        """
        try:
            algorithm = algorithm_registry.create(algorithm_name)
            return algorithm.configure(parameters)
        except Exception:
            return False
    
    def run_algorithm(self, algorithm_name: str, dataset_path: str,
                     parameters: Optional[Dict[str, Any]] = None,
                     task_id: Optional[int] = None) -> Dict[str, Any]:
        """
        运行指定算法分析数据
        
        Args:
            algorithm_name: 算法名称
            dataset_path: 数据集文件路径
            parameters: 算法参数
            task_id: 关联的任务ID（用于进度更新）
            
        Returns:
            Dict: 算法执行结果
            
        Raises:
            ValueError: 算法不存在或参数无效
            FileNotFoundError: 数据集文件不存在
            Exception: 算法执行失败
        """
        # 验证算法
        if algorithm_name not in algorithm_registry.list_algorithms():
            raise ValueError(f"不支持的算法: {algorithm_name}")
        
        # 验证数据集文件
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"数据集文件不存在: {dataset_path}")
        
        try:
            # 1. 更新任务进度 - 数据加载
            if task_id:
                self._update_task_progress(task_id, 10, "数据加载中")
            
            # 2. 加载数据
            df = pd.read_csv(dataset_path)
            if df.empty:
                raise ValueError("数据集为空")
            
            # 3. 特征提取
            if task_id:
                self._update_task_progress(task_id, 30, "特征提取中")
            
            features = self.feature_extractor.extract_features(df)
            features_scaled = self.feature_extractor.normalize_features(features)
            
            # 验证特征数据
            if features_scaled.shape[0] == 0:
                raise ValueError("特征提取后数据为空")
            
            # 4. 创建算法实例
            if task_id:
                self._update_task_progress(task_id, 50, "算法初始化")
            
            algorithm = algorithm_registry.create(algorithm_name)
            
            # 5. 参数配置
            if parameters:
                if not algorithm.configure(parameters):
                    raise ValueError("算法参数配置失败")
            
            # 6. 执行算法
            if task_id:
                self._update_task_progress(task_id, 70, "算法训练中")
            
            start_time = time.time()
            result = algorithm.fit(features_scaled)
            processing_time = time.time() - start_time
            
            # 7. 结果后处理
            if task_id:
                self._update_task_progress(task_id, 90, "结果处理中")
            
            processed_result = self._process_algorithm_result(
                result, features_scaled, len(df), processing_time, algorithm_name
            )
            
            # 8. 完成
            if task_id:
                self._update_task_progress(task_id, 100, "分析完成")
            
            return processed_result
            
        except Exception as e:
            if task_id:
                self._mark_task_failed(task_id, str(e))
            raise e
    
    def _process_algorithm_result(self, result: Dict[str, Any], 
                                features: np.ndarray, total_count: int,
                                processing_time: float, algorithm_name: str) -> Dict[str, Any]:
        """
        处理算法结果，统一格式和计算评估指标
        
        Args:
            result: 算法原始结果
            features: 标准化后的特征数据
            total_count: 总样本数
            processing_time: 处理时间
            algorithm_name: 算法名称
            
        Returns:
            Dict: 处理后的结果
        """
        # 提取基本信息
        labels = result.get('labels', [])
        bot_count = result.get('bot_addresses_count', 0)
        noise_points = result.get('noise_points', 0)
        
        # 计算轮廓系数
        silhouette = 0.0
        if labels is not None and len(labels) > 0:
            # 转换为numpy数组
            if not isinstance(labels, np.ndarray):
                labels = np.array(labels)
            
            # 计算轮廓系数（需要至少2个不同的聚类）
            unique_labels = np.unique(labels)
            if len(unique_labels) > 1:
                try:
                    # 过滤噪声点（标签为-1）
                    valid_indices = labels != -1
                    if np.sum(valid_indices) > 1 and len(np.unique(labels[valid_indices])) > 1:
                        silhouette = silhouette_score(features[valid_indices], labels[valid_indices])
                except Exception:
                    silhouette = 0.0
        
        # 计算聚类统计
        clusters_count = result.get('clusters_count', 0)
        normal_count = total_count - bot_count
        
        # 封装完整结果
        processed_result = {
            # 算法信息
            'algorithm_name': algorithm_name,
            'processing_time': round(processing_time, 3),
            
            # 聚类结果
            'clusters_count': int(clusters_count),
            'cluster_labels': labels.tolist() if isinstance(labels, np.ndarray) else labels,
            'cluster_stats': self._convert_to_json_serializable(result.get('cluster_stats', {})),
            
            # 检测结果统计
            'total_addresses': int(total_count),
            'bot_addresses_count': int(bot_count),
            'bot_addresses_pct': round((bot_count / total_count) * 100, 2) if total_count > 0 else 0,
            'normal_addresses_count': int(normal_count),
            'normal_addresses_pct': round((normal_count / total_count) * 100, 2) if total_count > 0 else 0,
            'noise_points': int(noise_points),
            'noise_points_pct': round((noise_points / total_count) * 100, 2) if total_count > 0 else 0,
            
            # 评估指标
            'silhouette_score': round(silhouette, 4),
            'detection_accuracy': 0.0,  # 无监督学习不计算准确率
            
            # 元数据
            'feature_count': int(features.shape[1]),
            'data_format': self.feature_extractor.data_format or 'Unknown',  # 使用已检测的格式
            
            # 详细指标
            'evaluation_metrics': self._convert_to_json_serializable({
                'silhouette_score': round(silhouette, 4),
                'inertia': result.get('inertia', 0),
                'detection_accuracy': 0.0
            })
        }
        
        return processed_result
    
    def _update_task_progress(self, task_id: int, progress: int, stage: str):
        """
        更新任务进度（需要数据库模型支持）
        
        Args:
            task_id: 任务ID
            progress: 进度百分比
            stage: 当前阶段描述
        """
        # 这里需要导入Task模型并更新
        # 为了避免循环导入，可以使用延迟导入
        try:
            from ..models import Task, db
            task = Task.query.get(task_id)
            if task:
                task.progress = progress
                task.current_stage = stage
                db.session.commit()
        except ImportError:
            # 如果模型还未实现，暂时跳过
            pass
        except Exception:
            # 数据库操作失败，记录日志但不影响主流程
            pass
    
    def _mark_task_failed(self, task_id: int, error_message: str):
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
        """
        try:
            from ..models import Task, db
            from datetime import datetime
            
            task = Task.query.get(task_id)
            if task:
                task.status = 'failed'
                task.error_message = error_message
                task.completed_at = datetime.utcnow()
                db.session.commit()
        except ImportError:
            pass
        except Exception:
            pass
    
    def get_algorithm_performance_stats(self) -> Dict[str, Any]:
        """
        获取算法性能统计信息
        
        Returns:
            Dict: 性能统计数据
        """
        # 这里可以从数据库查询历史结果，计算统计信息
        # 目前返回模拟数据结构
        return {
            'total_executions': 0,
            'average_processing_time': 0.0,
            'average_silhouette_score': 0.0,
            'algorithm_usage_stats': {},
            'success_rate': 0.0
        }
    
    def _convert_to_json_serializable(self, obj):
        """
        将包含numpy类型的数据结构转换为JSON可序列化的格式
        
        Args:
            obj: 要转换的对象
            
        Returns:
            JSON可序列化的对象
        """
        if isinstance(obj, dict):
            return {key: self._convert_to_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj