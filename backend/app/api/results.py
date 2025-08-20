"""
结果API路由
"""
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import api_bp
from ..models.result import Result
from ..models.task import Task
from .. import db


@api_bp.route('/results', methods=['GET'])
@jwt_required()
def get_results():
    """获取当前用户的分析结果列表"""
    user_id = get_jwt_identity()
    
    try:
        # 通过任务关联获取用户的结果
        results = db.session.query(Result).join(Task).filter(
            Task.user_id == user_id
        ).order_by(Result.created_at.desc()).all()
        
        return jsonify({
            'results': [result.to_dict() for result in results],
            'count': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({'message': '获取结果列表失败'}), 500


@api_bp.route('/results/<int:result_id>', methods=['GET'])
@jwt_required()
def get_result(result_id):
    """获取指定结果的详细信息"""
    user_id = get_jwt_identity()
    
    # 验证结果是否存在且属于当前用户
    result = db.session.query(Result).join(Task).filter(
        Result.id == result_id,
        Task.user_id == user_id
    ).first()
    
    if not result:
        return jsonify({'message': '结果不存在或无权限访问'}), 404
    
    result_dict = result.to_dict()
    
    # 添加任务和数据集信息
    if result.task:
        task_info = result.task.to_dict()
        if result.task.dataset:
            task_info['dataset'] = result.task.dataset.to_dict()
        result_dict['task'] = task_info
    
    return jsonify({'result': result_dict}), 200


@api_bp.route('/results/task/<int:task_id>', methods=['GET'])
@jwt_required()
def get_results_by_task(task_id):
    """获取指定任务的所有结果"""
    user_id = get_jwt_identity()
    
    # 验证任务是否存在且属于当前用户
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'message': '任务不存在或无权限访问'}), 404
    
    try:
        results = Result.query.filter_by(task_id=task_id).order_by(Result.created_at.desc()).all()
        
        return jsonify({
            'task': task.to_dict(),
            'results': [result.to_dict() for result in results],
            'count': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({'message': '获取任务结果失败'}), 500


@api_bp.route('/results/<int:result_id>', methods=['DELETE'])
@jwt_required()
def delete_result(result_id):
    """删除指定结果"""
    user_id = get_jwt_identity()
    
    # 验证结果是否存在且属于当前用户
    result = db.session.query(Result).join(Task).filter(
        Result.id == result_id,
        Task.user_id == user_id
    ).first()
    
    if not result:
        return jsonify({'message': '结果不存在或无权限访问'}), 404
    
    try:
        db.session.delete(result)
        db.session.commit()
        
        return jsonify({'message': '结果删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': '结果删除失败'}), 500


@api_bp.route('/results/comparison', methods=['POST'])
@jwt_required()
def compare_results():
    """对比多个分析结果"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    result_ids = data.get('result_ids', [])
    if not result_ids or len(result_ids) < 2:
        return jsonify({'message': '请选择至少2个结果进行对比'}), 400
    
    try:
        # 验证所有结果都属于当前用户
        results = db.session.query(Result).join(Task).filter(
            Result.id.in_(result_ids),
            Task.user_id == user_id
        ).all()
        
        if len(results) != len(result_ids):
            return jsonify({'message': '部分结果不存在或无权限访问'}), 404
        
        # 构建对比数据
        comparison_data = {
            'results': [],
            'metrics_comparison': {
                'silhouette_scores': [],
                'detection_rates': [],
                'processing_times': [],
                'algorithm_names': []
            },
            'summary': {
                'best_silhouette': None,
                'best_detection_rate': None,
                'fastest_processing': None,
                'recommendations': []
            }
        }
        
        for result in results:
            result_dict = result.to_dict()
            if result.task:
                result_dict['task_name'] = result.task.name
                if result.task.dataset:
                    result_dict['dataset_name'] = result.task.dataset.name
            
            comparison_data['results'].append(result_dict)
            
            # 收集指标数据
            comparison_data['metrics_comparison']['silhouette_scores'].append({
                'result_id': result.id,
                'algorithm': result.algorithm_name,
                'value': result.silhouette_score
            })
            comparison_data['metrics_comparison']['detection_rates'].append({
                'result_id': result.id,
                'algorithm': result.algorithm_name,
                'value': result.bot_addresses_pct
            })
            comparison_data['metrics_comparison']['processing_times'].append({
                'result_id': result.id,
                'algorithm': result.algorithm_name,
                'value': result.processing_time
            })
            comparison_data['metrics_comparison']['algorithm_names'].append(result.algorithm_name)
        
        # 计算最佳结果
        best_silhouette = max(results, key=lambda r: r.silhouette_score or 0)
        best_detection = max(results, key=lambda r: r.bot_addresses_pct)
        fastest = min(results, key=lambda r: r.processing_time)
        
        comparison_data['summary']['best_silhouette'] = {
            'result_id': best_silhouette.id,
            'algorithm': best_silhouette.algorithm_name,
            'value': best_silhouette.silhouette_score
        }
        comparison_data['summary']['best_detection_rate'] = {
            'result_id': best_detection.id,
            'algorithm': best_detection.algorithm_name,
            'value': best_detection.bot_addresses_pct
        }
        comparison_data['summary']['fastest_processing'] = {
            'result_id': fastest.id,
            'algorithm': fastest.algorithm_name,
            'value': fastest.processing_time
        }
        
        # 生成推荐
        recommendations = []
        if best_silhouette.silhouette_score and best_silhouette.silhouette_score > 0.3:
            recommendations.append(f"{best_silhouette.algorithm_name} 在聚类质量方面表现最佳")
        
        if best_detection.bot_addresses_pct >= 2 and best_detection.bot_addresses_pct <= 15:
            recommendations.append(f"{best_detection.algorithm_name} 的检测率在合理范围内")
        
        if fastest.processing_time < 1.0:
            recommendations.append(f"{fastest.algorithm_name} 在处理速度方面最优")
        
        comparison_data['summary']['recommendations'] = recommendations
        
        return jsonify(comparison_data), 200
        
    except Exception as e:
        return jsonify({'message': '结果对比失败'}), 500


@api_bp.route('/results/statistics', methods=['GET'])
@jwt_required()
def get_results_statistics():
    """获取结果统计信息"""
    user_id = get_jwt_identity()
    
    try:
        # 获取用户的所有结果
        results = db.session.query(Result).join(Task).filter(
            Task.user_id == user_id
        ).all()
        
        if not results:
            return jsonify({
                'total_results': 0,
                'algorithm_stats': {},
                'quality_distribution': {},
                'performance_metrics': {}
            }), 200
        
        # 算法使用统计
        algorithm_stats = {}
        for result in results:
            algo = result.algorithm_name
            if algo not in algorithm_stats:
                algorithm_stats[algo] = {
                    'count': 0,
                    'avg_silhouette': 0,
                    'avg_detection_rate': 0,
                    'avg_processing_time': 0
                }
            algorithm_stats[algo]['count'] += 1
        
        # 计算各算法平均指标
        for algo in algorithm_stats:
            algo_results = [r for r in results if r.algorithm_name == algo]
            
            silhouette_scores = [r.silhouette_score for r in algo_results if r.silhouette_score is not None]
            detection_rates = [r.bot_addresses_pct for r in algo_results]
            processing_times = [r.processing_time for r in algo_results]
            
            algorithm_stats[algo]['avg_silhouette'] = round(sum(silhouette_scores) / len(silhouette_scores), 3) if silhouette_scores else 0
            algorithm_stats[algo]['avg_detection_rate'] = round(sum(detection_rates) / len(detection_rates), 2)
            algorithm_stats[algo]['avg_processing_time'] = round(sum(processing_times) / len(processing_times), 3)
        
        # 质量分布
        quality_distribution = {
            'excellent': 0,  # > 0.7
            'good': 0,       # 0.3 - 0.7
            'fair': 0,       # 0.1 - 0.3
            'poor': 0        # < 0.1
        }
        
        for result in results:
            if result.silhouette_score is not None:
                if result.silhouette_score > 0.7:
                    quality_distribution['excellent'] += 1
                elif result.silhouette_score > 0.3:
                    quality_distribution['good'] += 1
                elif result.silhouette_score > 0.1:
                    quality_distribution['fair'] += 1
                else:
                    quality_distribution['poor'] += 1
        
        # 整体性能指标
        all_silhouette_scores = [r.silhouette_score for r in results if r.silhouette_score is not None]
        all_detection_rates = [r.bot_addresses_pct for r in results]
        all_processing_times = [r.processing_time for r in results]
        
        performance_metrics = {
            'avg_silhouette_score': round(sum(all_silhouette_scores) / len(all_silhouette_scores), 3) if all_silhouette_scores else 0,
            'avg_detection_rate': round(sum(all_detection_rates) / len(all_detection_rates), 2),
            'avg_processing_time': round(sum(all_processing_times) / len(all_processing_times), 3),
            'best_silhouette_score': max(all_silhouette_scores) if all_silhouette_scores else 0,
            'best_detection_rate': max(all_detection_rates) if all_detection_rates else 0,
            'fastest_processing_time': min(all_processing_times) if all_processing_times else 0
        }
        
        return jsonify({
            'total_results': len(results),
            'algorithm_stats': algorithm_stats,
            'quality_distribution': quality_distribution,
            'performance_metrics': performance_metrics
        }), 200
        
    except Exception as e:
        return jsonify({'message': '获取统计信息失败'}), 500


@api_bp.route('/results/<int:result_id>/export', methods=['GET'])
@jwt_required()
def export_result(result_id):
    """导出分析结果"""
    user_id = get_jwt_identity()
    
    # 验证结果是否存在且属于当前用户
    result = db.session.query(Result).join(Task).filter(
        Result.id == result_id,
        Task.user_id == user_id
    ).first()
    
    if not result:
        return jsonify({'message': '结果不存在或无权限访问'}), 404
    
    try:
        # 构建导出数据
        export_data = {
            'metadata': {
                'result_id': result.id,
                'algorithm_name': result.algorithm_name,
                'created_at': result.created_at.isoformat(),
                'task_name': result.task.name if result.task else 'Unknown',
                'dataset_name': result.task.dataset.name if result.task and result.task.dataset else 'Unknown'
            },
            'analysis_summary': {
                'total_addresses': result.total_addresses,
                'clusters_count': result.clusters_count,
                'bot_addresses_count': result.bot_addresses_count,
                'bot_addresses_percentage': result.bot_addresses_pct,
                'normal_addresses_count': result.normal_addresses_count,
                'normal_addresses_percentage': result.normal_addresses_pct,
                'noise_points': result.noise_points,
                'noise_points_percentage': result.noise_points_pct
            },
            'quality_metrics': {
                'silhouette_score': result.silhouette_score,
                'detection_accuracy': result.detection_accuracy,
                'processing_time': result.processing_time,
                'feature_count': result.feature_count,
                'data_format': result.data_format
            },
            'detailed_results': {
                'cluster_labels': result.cluster_labels,
                'cluster_statistics': result.cluster_stats,
                'evaluation_metrics': result.evaluation_metrics
            }
        }
        
        return jsonify({
            'message': '结果导出成功',
            'export_data': export_data
        }), 200
        
    except Exception as e:
        return jsonify({'message': '结果导出失败'}), 500