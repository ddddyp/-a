"""
特征提取器
负责从原始数据中提取和处理特征，支持多种数据格式
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from sklearn.preprocessing import RobustScaler, StandardScaler
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """基础特征提取器"""
    
    def __init__(self):
        self.scaler = None
        self.feature_names = []
        self.data_format = None
        self.is_fitted = False
        
    def detect_data_format(self, df: pd.DataFrame) -> str:
        """
        自动检测数据格式
        
        Args:
            df: 输入数据框
            
        Returns:
            str: 数据格式类型 (BLTE, Transaction, Generic)
        """
        columns = df.columns.tolist()
        
        # BLTE格式特征检测
        blte_keywords = ['degree', 'transaction', 'balance', 'time', 'clustering', 'entropy']
        blte_match_count = sum(1 for col in columns for keyword in blte_keywords if keyword.lower() in col.lower())
        
        # Transaction格式特征检测
        transaction_keywords = ['from', 'to', 'value', 'timestamp', 'hash', 'block']
        transaction_match_count = sum(1 for col in columns for keyword in transaction_keywords if keyword.lower() in col.lower())
        
        if blte_match_count >= 3:
            return 'BLTE'
        elif transaction_match_count >= 3:
            return 'Transaction'
        else:
            return 'Generic'
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        根据数据格式提取特征
        
        Args:
            df: 输入数据框
            
        Returns:
            pd.DataFrame: 提取后的特征
        """
        self.data_format = self.detect_data_format(df)
        
        if self.data_format == 'BLTE':
            return self.extract_blte_features(df)
        elif self.data_format == 'Transaction':
            return self.extract_transaction_features(df)
        else:
            return self.extract_generic_features(df)
    
    def extract_blte_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取BLTE格式特征"""
        # 直接使用数值列作为特征
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        features = df[numeric_columns].copy()
        
        # 处理缺失值
        features = features.fillna(features.median())
        
        self.feature_names = numeric_columns
        return features
    
    def extract_transaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取Transaction格式特征"""
        features = pd.DataFrame()
        
        # 基本统计特征
        if 'value' in df.columns:
            # 交易金额特征
            features['total_value'] = df.groupby('from')['value'].sum() if 'from' in df.columns else df['value'].sum()
            features['avg_value'] = df.groupby('from')['value'].mean() if 'from' in df.columns else df['value'].mean()
            features['max_value'] = df.groupby('from')['value'].max() if 'from' in df.columns else df['value'].max()
            features['min_value'] = df.groupby('from')['value'].min() if 'from' in df.columns else df['value'].min()
        
        # 如果有地址信息，计算度数特征
        if 'from' in df.columns and 'to' in df.columns:
            from_counts = df.groupby('from').size()
            to_counts = df.groupby('to').size()
            
            features['out_degree'] = from_counts
            features['in_degree'] = to_counts.reindex(from_counts.index, fill_value=0)
        
        # 填充缺失值
        features = features.fillna(0)
        
        self.feature_names = features.columns.tolist()
        return features
    
    def extract_generic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取通用格式特征"""
        # 选择数值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_columns:
            raise ValueError("没有找到数值列")
        
        features = df[numeric_columns].copy()
        
        # 处理缺失值
        features = features.fillna(features.median())
        
        self.feature_names = numeric_columns
        return features
    
    def normalize_features(self, features: pd.DataFrame, method: str = 'robust') -> np.ndarray:
        """
        特征标准化
        
        Args:
            features: 特征数据框
            method: 标准化方法 ('robust', 'standard')
            
        Returns:
            np.ndarray: 标准化后的特征
        """
        if method == 'robust':
            self.scaler = RobustScaler()
        else:
            self.scaler = StandardScaler()
        
        # 转换为numpy数组
        feature_array = features.values
        
        # 拟合和转换
        normalized_features = self.scaler.fit_transform(feature_array)
        self.is_fitted = True
        
        return normalized_features
    
    def transform(self, features: pd.DataFrame) -> np.ndarray:
        """使用已拟合的标准化器转换新数据"""
        if not self.is_fitted:
            raise ValueError("特征提取器尚未拟合，请先调用normalize_features")
        
        feature_array = features.values
        return self.scaler.transform(feature_array)


class OptimizedFeatureExtractor(FeatureExtractor):
    """优化的特征提取器，基于文档中的15维优化特征"""
    
    def __init__(self):
        super().__init__()
        
        # 根据实际数据列名定义的15个高质量特征
        self.optimized_features = [
            'in_degree',                    # 入度
            'out_degree',                   # 出度
            'Mean time interval',           # 平均时间间隔
            'Total amount incoming',        # 总接收金额 
            'Total amount outgoing',        # 总发送金额
            'all_degree',                   # 总度数
            'Max amount incoming',          # 最大接收金额
            'Max amount outgoing',          # 最大发送金额
            'Min amount incoming',          # 最小接收金额
            'Min amount outgoing',          # 最小发送金额
            'Avg amount incoming',          # 平均接收金额
            'Avg amount outgoing',          # 平均发送金额
            'Avg time incoming',            # 平均接收时间
            'Avg time outgoing',            # 平均发送时间
            'Active Duration'               # 活跃持续时间
        ]
        
        # 要移除的低质量特征（根据实际数据列名）
        self.features_to_remove = [
            'unique out_degree',        # out_degree的完全副本
            'unique in_degree',         # in_degree的完全副本
            'Clustering coefficient',   # 方差极低
            'Min time interval',        # 低方差特征
            'Max time interval',        # 分布极端不均
            'Total transaction time',   # 冗余特征
            'Avg gas price',           # 可能与交易行为无关
            'Avg gas limit',           # 可能与交易行为无关
            'Scam'                     # 标签列，不应作为特征
        ]
    
    def extract_blte_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取优化的BLTE特征"""
        # 选择数值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # 移除低质量特征
        selected_columns = [col for col in numeric_columns if col not in self.features_to_remove]
        
        # 如果有预定义的优化特征，优先使用
        available_optimized = [col for col in self.optimized_features if col in df.columns]
        if available_optimized:
            selected_columns = available_optimized
        
        features = df[selected_columns].copy()
        
        # 时间特征对数变换（解决量级差异问题）
        time_features = ['Mean time interval', 'Avg time incoming', 'Avg time outgoing', 'Active Duration']
        for time_col in time_features:
            if time_col in features.columns:
                # 对数变换：log(x+1) 避免log(0)
                features[time_col] = np.log1p(features[time_col])
        
        # 异常值处理 (3-Sigma规则)
        features = self._remove_outliers(features)
        
        # 处理缺失值
        features = features.fillna(features.median())
        
        self.feature_names = selected_columns
        
        logger.info(f"提取了 {len(selected_columns)} 个优化特征: {selected_columns}")
        
        return features
    
    def _remove_outliers(self, df: pd.DataFrame, sigma: float = 3.0) -> pd.DataFrame:
        """
        使用3-Sigma规则移除异常值
        
        Args:
            df: 输入数据框
            sigma: 标准差倍数
            
        Returns:
            pd.DataFrame: 处理后的数据框
        """
        df_clean = df.copy()
        
        for column in df.columns:
            if df[column].dtype in ['float64', 'int64']:
                mean = df[column].mean()
                std = df[column].std()
                
                # 定义异常值边界
                lower_bound = mean - sigma * std
                upper_bound = mean + sigma * std
                
                # 将异常值替换为边界值
                df_clean[column] = df_clean[column].clip(lower=lower_bound, upper=upper_bound)
        
        return df_clean
    
    def feature_quality_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        特征质量分析
        
        Args:
            df: 输入数据框
            
        Returns:
            Dict: 特征质量分析结果
        """
        analysis_results = {}
        
        # 数值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # 相关性分析
        correlation_matrix = df[numeric_columns].corr()
        high_corr_pairs = []
        
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.95:
                    high_corr_pairs.append({
                        'feature1': correlation_matrix.columns[i],
                        'feature2': correlation_matrix.columns[j],
                        'correlation': corr_value
                    })
        
        # 方差分析
        variances = df[numeric_columns].var()
        low_variance_features = variances[variances < 1e-4].index.tolist()
        
        # 缺失值分析
        missing_analysis = df.isnull().sum()
        high_missing_features = missing_analysis[missing_analysis > len(df) * 0.5].index.tolist()
        
        analysis_results = {
            'total_features': len(numeric_columns),
            'high_correlation_pairs': high_corr_pairs,
            'low_variance_features': low_variance_features,
            'high_missing_features': high_missing_features,
            'feature_variances': variances.to_dict(),
            'missing_counts': missing_analysis.to_dict()
        }
        
        return analysis_results
    
    def get_feature_importance(self, features: pd.DataFrame) -> Dict[str, float]:
        """
        基于PCA计算特征重要性
        
        Args:
            features: 特征数据框
            
        Returns:
            Dict: 特征重要性字典
        """
        try:
            from sklearn.decomposition import PCA
            
            # 标准化特征
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # PCA分析
            pca = PCA()
            pca.fit(features_scaled)
            
            # 计算特征重要性 (基于主成分贡献)
            importance_scores = {}
            for i, feature_name in enumerate(features.columns):
                # 计算该特征在前几个主成分中的贡献
                importance = np.sum(np.abs(pca.components_[:3, i]) * pca.explained_variance_ratio_[:3])
                importance_scores[feature_name] = importance
            
            return importance_scores
            
        except ImportError:
            logger.warning("sklearn.decomposition.PCA 不可用，跳过特征重要性分析")
            return {}
        except Exception as e:
            logger.error(f"特征重要性计算失败: {e}")
            return {}


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证数据框的质量和有效性
        
        Args:
            df: 输入数据框
            
        Returns:
            Dict: 验证结果
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # 基本检查
        if df.empty:
            validation_results['is_valid'] = False
            validation_results['errors'].append("数据框为空")
            return validation_results
        
        # 数值列检查
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_columns:
            validation_results['is_valid'] = False
            validation_results['errors'].append("没有找到数值列")
            return validation_results
        
        # 统计信息
        validation_results['statistics'] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'numeric_columns': len(numeric_columns),
            'missing_values': df.isnull().sum().sum(),
            'duplicate_rows': df.duplicated().sum()
        }
        
        # 检查无穷值和NaN
        for col in numeric_columns:
            if df[col].isnull().all():
                validation_results['warnings'].append(f"列 '{col}' 全部为空值")
            elif np.isinf(df[col]).any():
                validation_results['warnings'].append(f"列 '{col}' 包含无穷值")
            elif df[col].var() == 0:
                validation_results['warnings'].append(f"列 '{col}' 方差为0（常数列）")
        
        # 样本数量检查
        if len(df) < 10:
            validation_results['warnings'].append("样本数量过少（<10），可能影响分析结果")
        
        return validation_results