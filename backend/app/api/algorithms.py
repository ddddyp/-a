"""
算法API路由
"""
from flask import jsonify
from flask_jwt_extended import jwt_required

from . import api_bp
import sys
import os
# Add parent directory to path to access training module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from training.algorithms import algorithm_registry


@api_bp.route('/algorithms', methods=['GET'])
@jwt_required()
def get_algorithms():
    """获取所有可用算法"""
    algorithms_info = {}
    
    for algorithm_name in algorithm_registry.list_algorithms():
        try:
            info = algorithm_registry.get_algorithm_info(algorithm_name)
            algorithms_info[algorithm_name] = info
        except Exception as e:
            algorithms_info[algorithm_name] = {'error': str(e)}
    
    return jsonify({
        'algorithms': algorithms_info,
        'count': len(algorithms_info)
    }), 200


@api_bp.route('/algorithms/<algorithm_name>/info', methods=['GET'])
@jwt_required() 
def get_algorithm_info(algorithm_name):
    """获取指定算法的详细信息"""
    try:
        info = algorithm_registry.get_algorithm_info(algorithm_name)
        
        # 获取算法实例以获取默认参数
        algorithm = algorithm_registry.create(algorithm_name)
        default_params = algorithm.get_params()
        
        info['default_parameters'] = default_params
        
        # 添加算法特性说明
        algorithm_features = {
            'DBSCAN': {
                'type': '密度聚类',
                'strengths': ['处理非凸形状聚类', '自动识别噪声点', '无需预设聚类数量'],
                'weaknesses': ['对参数敏感', '不同密度聚类效果差'],
                'best_for': ['区块链交易行为分组', '异常模式识别']
            },
            'IsolationForest': {
                'type': '异常检测',
                'strengths': ['专门检测异常', '适合稀疏异常模式', '线性时间复杂度'],
                'weaknesses': ['只能二分类', '对正常数据密度敏感'],
                'best_for': ['机器人账户检测', '欺诈行为识别']
            },
            'KmeansPlus': {
                'type': '质心聚类',
                'strengths': ['稳定可靠', '可解释性强', '聚类中心明确'],
                'weaknesses': ['需要预设K值', '对离群点敏感', '假设球形聚类'],
                'best_for': ['用户行为分类', '基准性能对比']
            }
        }
        
        if algorithm_name in algorithm_features:
            info['features'] = algorithm_features[algorithm_name]
        
        return jsonify({'algorithm': info}), 200
        
    except ValueError as e:
        return jsonify({'message': str(e)}), 404
    except Exception as e:
        return jsonify({'message': '获取算法信息失败'}), 500


@api_bp.route('/algorithms/<algorithm_name>/parameters', methods=['GET'])
@jwt_required()
def get_algorithm_parameters(algorithm_name):
    """获取算法参数配置"""
    try:
        algorithm = algorithm_registry.create(algorithm_name)
        params = algorithm.get_params()
        
        # 为每个算法提供参数说明
        parameter_descriptions = {
            'DBSCAN': {
                'eps': {
                    'description': '邻域半径，控制聚类的紧密程度',
                    'type': 'float or "auto"',
                    'default': 'auto',
                    'range': '(0, inf)',
                    'auto_description': '使用K-距离图自动选择'
                },
                'min_samples': {
                    'description': '形成聚类的最小样本数',
                    'type': 'int or "auto"',
                    'default': 'auto',
                    'range': '[2, inf)',
                    'auto_description': '基于特征维度自动计算'
                },
                'metric': {
                    'description': '距离度量方式',
                    'type': 'string',
                    'default': 'euclidean',
                    'options': ['euclidean', 'manhattan', 'cosine']
                }
            },
            'IsolationForest': {
                'contamination': {
                    'description': '异常样本比例',
                    'type': 'float or "auto"',
                    'default': 'auto',
                    'range': '(0, 0.5)',
                    'auto_description': '基于数据规模自适应调整'
                },
                'n_estimators': {
                    'description': '隔离树的数量',
                    'type': 'int or "auto"',
                    'default': 'auto',
                    'range': '[10, 1000]',
                    'auto_description': '根据样本数量自动选择'
                },
                'max_samples': {
                    'description': '每棵树的最大样本数',
                    'type': 'int or "auto"',
                    'default': 'auto',
                    'range': '[1, n_samples]',
                    'auto_description': '自动设为min(256, n_samples)'
                }
            },
            'KmeansPlus': {
                'n_clusters': {
                    'description': '聚类数量',
                    'type': 'int or "auto"',
                    'default': 'auto',
                    'range': '[2, inf)',
                    'auto_description': '使用多准则方法自动选择'
                },
                'init': {
                    'description': '初始化方法',
                    'type': 'string',
                    'default': 'k-means++',
                    'options': ['k-means++', 'random']
                },
                'max_iter': {
                    'description': '最大迭代次数',
                    'type': 'int',
                    'default': 300,
                    'range': '[1, 1000]'
                },
                'k_range': {
                    'description': 'K值搜索范围',
                    'type': 'tuple',
                    'default': '(2, 10)',
                    'format': '(min_k, max_k)'
                }
            }
        }
        
        descriptions = parameter_descriptions.get(algorithm_name, {})
        
        return jsonify({
            'algorithm_name': algorithm_name,
            'parameters': params,
            'parameter_descriptions': descriptions
        }), 200
        
    except ValueError as e:
        return jsonify({'message': str(e)}), 404
    except Exception as e:
        return jsonify({'message': '获取参数配置失败'}), 500


@api_bp.route('/algorithms/comparison', methods=['GET'])
@jwt_required()
def get_algorithms_comparison():
    """获取算法对比信息"""
    try:
        comparison_data = {
            'performance_metrics': {
                'DBSCAN': {
                    'silhouette_score': 0.571,
                    'detection_rate': '3.9%',
                    'processing_time': '0.105s',
                    'quality_rating': 4,
                    'complexity': 'O(n log n)'
                },
                'IsolationForest': {
                    'silhouette_score': 0.622,
                    'detection_rate': '8.0%',
                    'processing_time': '0.283s',
                    'quality_rating': 5,
                    'complexity': 'O(n)'
                },
                'KmeansPlus': {
                    'silhouette_score': 0.571,
                    'detection_rate': '7.5%',
                    'processing_time': '1.459s',
                    'quality_rating': 4,
                    'complexity': 'O(n*k*i)'
                }
            },
            'use_cases': {
                'DBSCAN': ['密度不均匀数据', '噪声数据处理', '不规则形状聚类'],
                'IsolationForest': ['异常检测', '欺诈识别', '机器人检测'],
                'KmeansPlus': ['基准分析', '用户分类', '行为模式识别']
            },
            'recommendations': {
                'best_overall': 'IsolationForest',
                'fastest': 'DBSCAN',
                'most_stable': 'KmeansPlus',
                'best_for_beginners': 'KmeansPlus'
            }
        }
        
        return jsonify(comparison_data), 200
        
    except Exception as e:
        return jsonify({'message': '获取对比信息失败'}), 500