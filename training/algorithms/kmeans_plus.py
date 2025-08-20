"""
KmeansPlus算法实现
改进的K-means聚类算法，使用多准则K值选择和智能初始化
"""
import numpy as np
import time
from typing import Dict, Any, List, Tuple
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import matplotlib.pyplot as plt

from .base import BaseAlgorithm, algorithm_registry


class KmeansPlusAlgorithm(BaseAlgorithm):
    """KmeansPlus聚类算法"""
    
    def __init__(self, name: str = "KmeansPlus"):
        super().__init__(name)
        self.model = None
        self.optimal_k = None
        self.k_evaluation_results = None
        
        # 默认参数
        self.parameters = {
            'n_clusters': 'auto',  # 自动选择或指定数值
            'init': 'k-means++',
            'n_init': 10,
            'max_iter': 300,
            'tol': 1e-4,
            'random_state': 42,
            'algorithm': 'lloyd',
            'n_jobs': -1,
            'k_range': (2, 10)  # K值搜索范围
        }
    
    def configure(self, params: Dict[str, Any]) -> bool:
        """配置KmeansPlus参数"""
        try:
            valid_params = ['n_clusters', 'init', 'n_init', 'max_iter', 'tol', 
                          'random_state', 'algorithm', 'n_jobs', 'k_range']
            for key, value in params.items():
                if key in valid_params:
                    self.parameters[key] = value
                else:
                    print(f"警告: 无效参数 {key}")
            return True
        except Exception as e:
            print(f"参数配置失败: {e}")
            return False
    
    def _elbow_method(self, X: np.ndarray, k_range: range) -> List[float]:
        """
        肘部法则计算WCSS (Within-Cluster Sum of Squares)
        
        Args:
            X: 输入数据
            k_range: K值范围
            
        Returns:
            List[float]: 每个K值对应的WCSS
        """
        wcss_list = []
        
        for k in k_range:
            try:
                kmeans = KMeans(
                    n_clusters=k,
                    init=self.parameters['init'],
                    n_init=self.parameters['n_init'],
                    max_iter=self.parameters['max_iter'],
                    tol=self.parameters['tol'],
                    random_state=self.parameters['random_state']
                )
                kmeans.fit(X)
                wcss_list.append(kmeans.inertia_)
            except:
                wcss_list.append(float('inf'))
        
        return wcss_list
    
    def _silhouette_method(self, X: np.ndarray, k_range: range) -> List[float]:
        """
        轮廓系数方法评估聚类质量
        
        Args:
            X: 输入数据
            k_range: K值范围
            
        Returns:
            List[float]: 每个K值对应的轮廓系数
        """
        silhouette_scores = []
        
        for k in k_range:
            try:
                if k >= len(X):  # K不能大于等于样本数
                    silhouette_scores.append(-1)
                    continue
                    
                kmeans = KMeans(
                    n_clusters=k,
                    init=self.parameters['init'],
                    n_init=self.parameters['n_init'],
                    max_iter=self.parameters['max_iter'],
                    tol=self.parameters['tol'],
                    random_state=self.parameters['random_state']
                )
                labels = kmeans.fit_predict(X)
                
                # 计算轮廓系数
                if len(set(labels)) > 1:
                    score = silhouette_score(X, labels)
                else:
                    score = -1
                
                silhouette_scores.append(score)
                
            except:
                silhouette_scores.append(-1)
        
        return silhouette_scores
    
    def _calinski_harabasz_method(self, X: np.ndarray, k_range: range) -> List[float]:
        """
        Calinski-Harabasz指数评估聚类质量
        
        Args:
            X: 输入数据
            k_range: K值范围
            
        Returns:
            List[float]: 每个K值对应的CH指数
        """
        ch_scores = []
        
        for k in k_range:
            try:
                if k >= len(X):
                    ch_scores.append(0)
                    continue
                
                kmeans = KMeans(
                    n_clusters=k,
                    init=self.parameters['init'],
                    n_init=self.parameters['n_init'],
                    max_iter=self.parameters['max_iter'],
                    tol=self.parameters['tol'],
                    random_state=self.parameters['random_state']
                )
                labels = kmeans.fit_predict(X)
                
                if len(set(labels)) > 1:
                    score = calinski_harabasz_score(X, labels)
                else:
                    score = 0
                
                ch_scores.append(score)
                
            except:
                ch_scores.append(0)
        
        return ch_scores
    
    def _multi_criteria_k_selection(self, X: np.ndarray) -> Tuple[int, Dict[str, Any]]:
        """
        多准则K值选择
        
        Args:
            X: 输入数据
            
        Returns:
            Tuple[int, Dict]: (最优K值, 评估结果)
        """
        k_min, k_max = self.parameters['k_range']
        k_max = min(k_max, len(X) - 1)  # 确保K值不超过样本数-1
        
        if k_min >= k_max:
            return 2, {'method': 'default', 'reason': 'insufficient_samples'}
        
        k_range = range(k_min, k_max + 1)
        
        # 计算多个评估指标
        wcss_scores = self._elbow_method(X, k_range)
        silhouette_scores = self._silhouette_method(X, k_range)
        ch_scores = self._calinski_harabasz_method(X, k_range)
        
        # 记录评估结果
        evaluation_results = {
            'k_range': list(k_range),
            'wcss_scores': wcss_scores,
            'silhouette_scores': silhouette_scores,
            'ch_scores': ch_scores
        }
        
        # 综合评分选择最优K
        best_k = k_min
        best_score = -float('inf')
        
        for i, k in enumerate(k_range):
            if silhouette_scores[i] <= 0:  # 跳过无效的轮廓系数
                continue
            
            # 标准化各项指标 (0-1范围)
            sil_score = silhouette_scores[i]
            
            # CH指数标准化
            ch_score = ch_scores[i]
            max_ch = max(ch_scores) if max(ch_scores) > 0 else 1
            ch_normalized = ch_score / max_ch
            
            # WCSS用肘部法则评估 (寻找拐点)
            wcss_score = 0
            if i > 0 and i < len(wcss_scores) - 1:
                # 计算二阶差分作为肘部指标
                diff1_prev = wcss_scores[i-1] - wcss_scores[i]
                diff1_next = wcss_scores[i] - wcss_scores[i+1]
                wcss_score = abs(diff1_prev - diff1_next) / max(wcss_scores)
            
            # 综合评分 (轮廓系数权重最高)
            composite_score = (0.6 * sil_score + 0.3 * ch_normalized + 0.1 * wcss_score)
            
            if composite_score > best_score:
                best_score = composite_score
                best_k = k
        
        evaluation_results['best_k'] = best_k
        evaluation_results['best_score'] = best_score
        evaluation_results['selection_method'] = 'multi_criteria'
        
        self.k_evaluation_results = evaluation_results
        
        return best_k, evaluation_results
    
    def fit(self, X: np.ndarray) -> Dict[str, Any]:
        """训练KmeansPlus模型"""
        try:
            # 验证输入
            self._validate_input(X)
            
            start_time = time.time()
            
            # K值选择
            if self.parameters['n_clusters'] == 'auto':
                optimal_k, k_eval_results = self._multi_criteria_k_selection(X)
                self.optimal_k = optimal_k
            else:
                optimal_k = self.parameters['n_clusters']
                k_eval_results = {'method': 'manual', 'k': optimal_k}
            
            # 创建和训练模型
            self.model = KMeans(
                n_clusters=optimal_k,
                init=self.parameters['init'],
                n_init=self.parameters['n_init'],
                max_iter=self.parameters['max_iter'],
                tol=self.parameters['tol'],
                random_state=self.parameters['random_state']
            )
            
            # 执行聚类
            labels = self.model.fit_predict(X)
            self.labels_ = labels
            self.is_fitted = True
            
            self.training_time = time.time() - start_time
            
            # 计算统计信息
            stats = self._calculate_statistics(labels)
            
            # 计算轮廓系数
            silhouette = 0.0
            if len(set(labels)) > 1:
                try:
                    silhouette = silhouette_score(X, labels)
                except:
                    silhouette = 0.0
            
            # 聚类详细统计
            unique_labels = np.unique(labels)
            cluster_stats = {}
            for label in unique_labels:
                mask = labels == label
                cluster_size = np.sum(mask)
                cluster_stats[f'聚类_{label}'] = {
                    'size': cluster_size,
                    'percentage': (cluster_size / len(labels)) * 100,
                    'center': self.model.cluster_centers_[label].tolist()
                }
            
            # 聚类质量指标
            quality_metrics = {
                'silhouette_score': silhouette,
                'inertia': float(self.model.inertia_),
                'n_iter': int(self.model.n_iter_)
            }
            
            # 添加其他质量指标
            try:
                quality_metrics['calinski_harabasz_score'] = calinski_harabasz_score(X, labels)
                quality_metrics['davies_bouldin_score'] = davies_bouldin_score(X, labels)
            except:
                pass
            
            result = {
                'algorithm_name': self.name,
                'labels': labels.tolist(),
                'clusters_count': len(unique_labels),
                'bot_addresses_count': stats['bot_addresses_count'],
                'normal_addresses_count': stats['normal_addresses_count'],
                'noise_points': 0,  # K-means没有噪声点概念
                'silhouette_score': silhouette,
                'cluster_stats': cluster_stats,
                'cluster_centers': self.model.cluster_centers_.tolist(),
                'quality_metrics': quality_metrics,
                'k_selection_results': k_eval_results,
                'parameters_used': {
                    'n_clusters': optimal_k,
                    'init': self.parameters['init'],
                    'n_init': self.parameters['n_init'],
                    'max_iter': self.parameters['max_iter']
                },
                'training_time': self.training_time
            }
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"KmeansPlus训练失败: {str(e)}")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测新数据的聚类标签"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练，请先调用fit方法")
        
        try:
            self._validate_input(X)
            return self.model.predict(X)
        except Exception as e:
            raise RuntimeError(f"预测失败: {str(e)}")
    
    def get_cluster_centers(self) -> np.ndarray:
        """获取聚类中心"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练")
        
        return self.model.cluster_centers_
    
    def evaluate(self, X: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
        """评估KmeansPlus性能"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练")
        
        try:
            metrics = {}
            
            # 轮廓系数
            if len(set(labels)) > 1:
                metrics['silhouette_score'] = silhouette_score(X, labels)
                metrics['calinski_harabasz_score'] = calinski_harabasz_score(X, labels)
                metrics['davies_bouldin_score'] = davies_bouldin_score(X, labels)
            else:
                metrics['silhouette_score'] = 0.0
            
            # 聚类数量
            metrics['n_clusters'] = len(set(labels))
            
            # 惯性(WCSS)
            metrics['inertia'] = float(self.model.inertia_)
            
            # 迭代次数
            metrics['n_iter'] = int(self.model.n_iter_)
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}


# 注册算法
algorithm_registry.register(
    KmeansPlusAlgorithm,
    name="KmeansPlus",
    description="改进的K-means聚类算法，支持自动K值选择和多准则评估",
    author="区块链",
    version="2.0"
)