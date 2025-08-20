"""
任务API路由
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import api_bp
from ..models.task import Task
from ..models.dataset import Dataset
from ..services.task_service import TaskService
import sys
import os
# Add parent directory to path to access training module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from training.algorithms import algorithm_registry
from .. import db


@api_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """获取当前用户的任务列表"""
    user_id = get_jwt_identity()
    
    try:
        tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks],
            'count': len(tasks)
        }), 200
        
    except Exception as e:
        return jsonify({'message': '获取任务列表失败'}), 500


@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """获取指定任务详情"""
    user_id = get_jwt_identity()
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'message': '任务不存在或无权限访问'}), 404
    
    task_dict = task.to_dict()
    
    # 添加数据集信息
    if task.dataset:
        task_dict['dataset'] = task.dataset.to_dict()
    
    # 添加结果信息
    if task.results.count() > 0:
        latest_result = task.results.order_by(task.results.property.mapper.class_.created_at.desc()).first()
        task_dict['latest_result'] = latest_result.to_dict()
    
    return jsonify({'task': task_dict}), 200


@api_bp.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    """创建新任务"""
    data = request.get_json()
    user_id = int(get_jwt_identity())
    
    # 验证必填字段
    required_fields = ['name', 'algorithm_name', 'dataset_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'{field} 不能为空'}), 400
    
    # 验证算法是否存在
    if data['algorithm_name'] not in algorithm_registry.list_algorithms():
        return jsonify({'message': '不支持的算法类型'}), 400
    
    # 验证数据集是否存在且属于当前用户
    dataset = Dataset.query.filter_by(
        id=data['dataset_id'], 
        user_id=user_id
    ).first()
    
    if not dataset:
        return jsonify({'message': '数据集不存在或无权限访问'}), 404
    
    if not dataset.is_valid:
        return jsonify({'message': '数据集验证失败，无法创建任务'}), 400
    
    try:
        # 创建任务数据库记录
        task = Task(
            name=data['name'],
            description=data.get('description', ''),
            algorithm_name=data['algorithm_name'],
            dataset_id=data['dataset_id'],
            user_id=user_id,
            parameters=data.get('parameters', {}),
            status='pending',
            progress=0,
            current_stage='等待执行'
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'message': '任务创建成功',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'任务创建失败: {str(e)}'}), 500


@api_bp.route('/tasks/<int:task_id>/start', methods=['POST'])
@jwt_required()
def start_task(task_id):
    """启动任务"""
    user_id = get_jwt_identity()
    
    # 验证任务存在且属于当前用户
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'message': '任务不存在或无权限访问'}), 404
    
    if task.status != 'pending':
        return jsonify({'message': f'任务状态为{task.status}，无法启动'}), 400
    
    # 构建数据集文件路径
    try:
        from flask import current_app
        import os
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        dataset_path = os.path.join(upload_folder, task.dataset.filename)
        
        if not os.path.exists(dataset_path):
            return jsonify({'message': '数据集文件不存在'}), 404
        
        # 标记任务开始运行
        task.mark_running()
        
        # 使用算法服务直接执行任务
        from ..services.algorithm_service import AlgorithmService
        algorithm_service = AlgorithmService(use_optimized_features=True)
        
        try:
            # 执行算法
            import time
            start_time = time.time()
            
            result = algorithm_service.run_algorithm(
                algorithm_name=task.algorithm_name,
                dataset_path=dataset_path,
                parameters=task.parameters or {},
                task_id=task_id
            )
            
            processing_time = time.time() - start_time
            
            # 标记任务完成
            task.mark_completed(processing_time)
            
            # 保存结果到数据库
            from ..models.result import Result
            result_record = Result(
                algorithm_name=task.algorithm_name,
                clusters_count=result.get('clusters_count', 0),
                bot_addresses_count=result.get('bot_addresses_count', 0),
                bot_addresses_pct=result.get('bot_addresses_pct', 0.0),
                normal_addresses_count=result.get('normal_addresses_count', 0),
                normal_addresses_pct=result.get('normal_addresses_pct', 0.0),
                noise_points=result.get('noise_points', 0),
                noise_points_pct=result.get('noise_points_pct', 0.0),
                silhouette_score=result.get('silhouette_score', 0.0),
                detection_accuracy=result.get('detection_accuracy', 0.0),
                cluster_labels=result.get('cluster_labels', []),
                cluster_stats=result.get('cluster_stats', {}),
                evaluation_metrics=result.get('evaluation_metrics', {}),
                total_addresses=result.get('total_addresses', 0),
                feature_count=result.get('feature_count', 0),
                data_format=result.get('data_format', 'Unknown'),
                processing_time=processing_time,
                task_id=task_id
            )
            
            db.session.add(result_record)
            db.session.commit()
            
            return jsonify({
                'message': '任务执行成功',
                'result': result_record.to_dict()
            }), 200
            
        except Exception as e:
            # 标记任务失败
            task.mark_failed(str(e))
            return jsonify({'message': f'任务执行失败: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'message': '任务启动失败'}), 500


@api_bp.route('/tasks/<int:task_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_task(task_id):
    """取消任务"""
    user_id = get_jwt_identity()
    
    # 验证任务存在且属于当前用户
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'message': '任务不存在或无权限访问'}), 404
    
    if task.status not in ['pending', 'running']:
        return jsonify({'message': f'任务状态为{task.status}，无法取消'}), 400
    
    try:
        # 直接更新任务状态为已取消
        task.status = 'cancelled'
        task.progress = 0
        task.current_stage = '已取消'
        task.completed_at = db.func.now()
        
        db.session.commit()
        
        return jsonify({'message': '任务取消成功'}), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'任务取消失败: {str(e)}'}), 500


@api_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """删除任务"""
    user_id = get_jwt_identity()
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'message': '任务不存在或无权限访问'}), 404
    
    if task.status == 'running':
        return jsonify({'message': '无法删除正在运行的任务'}), 400
    
    try:
        # 删除关联的结果
        for result in task.results:
            db.session.delete(result)
        
        # 删除任务
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': '任务删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': '任务删除失败'}), 500


@api_bp.route('/tasks/running', methods=['GET'])
@jwt_required()
def get_running_tasks():
    """获取当前运行中的任务"""
    user_id = get_jwt_identity()
    
    try:
        # 从数据库获取运行中的任务
        running_tasks = Task.query.filter_by(
            user_id=user_id, 
            status='running'
        ).order_by(Task.started_at.desc()).all()
        
        # 从任务服务获取实时状态
        task_service = TaskService()
        service_running_tasks = task_service.get_running_tasks()
        
        return jsonify({
            'tasks': [task.to_dict() for task in running_tasks],
            'count': len(running_tasks),
            'service_status': service_running_tasks
        }), 200
        
    except Exception as e:
        return jsonify({'message': '获取运行任务失败'}), 500


@api_bp.route('/tasks/statistics', methods=['GET'])
@jwt_required()
def get_tasks_statistics():
    """获取任务统计信息"""
    user_id = get_jwt_identity()
    
    try:
        user_tasks = Task.query.filter_by(user_id=user_id)
        
        # 状态统计
        status_stats = {}
        for status in ['pending', 'running', 'completed', 'failed', 'cancelled']:
            count = user_tasks.filter_by(status=status).count()
            if count > 0:
                status_stats[status] = count
        
        # 算法使用统计
        algorithm_stats = {}
        for algorithm in ['DBSCAN', 'IsolationForest', 'KmeansPlus']:
            count = user_tasks.filter_by(algorithm_name=algorithm).count()
            if count > 0:
                algorithm_stats[algorithm] = count
        
        # 成功率计算
        total_tasks = user_tasks.count()
        completed_tasks = user_tasks.filter_by(status='completed').count()
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 平均处理时间
        completed_tasks_with_time = user_tasks.filter(
            Task.status == 'completed',
            Task.processing_time.isnot(None)
        ).all()
        
        avg_processing_time = 0
        if completed_tasks_with_time:
            total_time = sum(task.processing_time for task in completed_tasks_with_time)
            avg_processing_time = total_time / len(completed_tasks_with_time)
        
        # 最近任务
        recent_tasks = user_tasks.order_by(Task.created_at.desc()).limit(5).all()
        
        return jsonify({
            'total_tasks': total_tasks,
            'status_stats': status_stats,
            'algorithm_stats': algorithm_stats,
            'success_rate': round(success_rate, 1),
            'avg_processing_time': round(avg_processing_time, 2),
            'recent_tasks': [task.to_dict() for task in recent_tasks]
        }), 200
        
    except Exception as e:
        return jsonify({'message': '获取统计信息失败'}), 500


@api_bp.route('/tasks/service/status', methods=['GET'])
@jwt_required()
def get_task_service_status():
    """获取任务服务状态"""
    try:
        task_service = TaskService()
        service_stats = task_service.get_service_statistics()
        
        return jsonify({
            'service_statistics': service_stats,
            'status': 'healthy' if service_stats.get('executor_alive', False) else 'unhealthy'
        }), 200
        
    except Exception as e:
        return jsonify({'message': '获取服务状态失败'}), 500