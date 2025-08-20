"""
数据集API路由
"""
import os
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from . import api_bp
from ..models.dataset import Dataset
from ..models.user import User
from ..services.data_service import DataService
from .. import db


@api_bp.route('/datasets', methods=['GET'])
@jwt_required()
def get_datasets():
    """获取当前用户的数据集列表"""
    user_id = get_jwt_identity()
    
    try:
        datasets = Dataset.query.filter_by(user_id=user_id).order_by(Dataset.upload_time.desc()).all()
        
        return jsonify({
            'datasets': [dataset.to_dict() for dataset in datasets],
            'count': len(datasets)
        }), 200
        
    except Exception as e:
        return jsonify({'message': '获取数据集列表失败'}), 500


@api_bp.route('/datasets/<int:dataset_id>', methods=['GET'])
@jwt_required()
def get_dataset(dataset_id):
    """获取指定数据集详情"""
    user_id = get_jwt_identity()
    
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first()
    if not dataset:
        return jsonify({'message': '数据集不存在或无权限访问'}), 404
    
    return jsonify({'dataset': dataset.to_dict()}), 200


@api_bp.route('/datasets/upload', methods=['POST'])
@jwt_required()
def upload_dataset():
    """上传数据集文件"""
    user_id = int(get_jwt_identity())
    
    # 检查文件是否存在
    if 'file' not in request.files:
        return jsonify({'message': '未选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': '未选择文件'}), 400
    
    # 获取其他表单数据
    name = request.form.get('name', file.filename)
    description = request.form.get('description', '')
    
    try:
        # 创建数据服务实例
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        data_service = DataService(upload_folder)
        
        # 保存文件并验证
        file_info = data_service.save_file(file, user_id)
        
        # 创建数据集记录
        dataset = Dataset(
            name=name,
            description=description,
            original_filename=file_info['original_filename'],
            filename=file_info['filename'],
            file_type=file_info['file_type'],
            file_size=file_info['file_size'],
            record_count=file_info['validation_info'].get('record_count'),
            column_count=file_info['validation_info'].get('column_count'),
            data_format=file_info['validation_info'].get('data_format'),
            is_valid=file_info['is_valid'],
            validation_info=file_info['validation_info'],
            user_id=user_id
        )
        
        db.session.add(dataset)
        db.session.commit()
        
        return jsonify({
            'message': '数据集上传成功',
            'dataset': dataset.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': '文件上传失败'}), 500


@api_bp.route('/datasets/<int:dataset_id>', methods=['PUT'])
@jwt_required()
def update_dataset(dataset_id):
    """更新数据集信息"""
    user_id = get_jwt_identity()
    
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first()
    if not dataset:
        return jsonify({'message': '数据集不存在或无权限访问'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'message': '无效的请求数据'}), 400
    
    try:
        # 更新可修改的字段
        if 'name' in data:
            dataset.name = data['name']
        if 'description' in data:
            dataset.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'message': '数据集更新成功',
            'dataset': dataset.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': '更新失败'}), 500


@api_bp.route('/datasets/<int:dataset_id>', methods=['DELETE'])
@jwt_required()
def delete_dataset(dataset_id):
    """删除数据集"""
    user_id = get_jwt_identity()
    
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first()
    if not dataset:
        return jsonify({'message': '数据集不存在或无权限访问'}), 404
    
    # 检查是否有关联的任务
    if dataset.tasks.count() > 0:
        return jsonify({'message': '无法删除：该数据集已被任务使用'}), 400
    
    try:
        # 删除文件
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        data_service = DataService(upload_folder)
        data_service.delete_file(dataset.filename)
        
        # 删除数据库记录
        db.session.delete(dataset)
        db.session.commit()
        
        return jsonify({'message': '数据集删除成功'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': '删除失败'}), 500


@api_bp.route('/datasets/<int:dataset_id>/preview', methods=['GET'])
@jwt_required()
def preview_dataset(dataset_id):
    """预览数据集内容"""
    user_id = get_jwt_identity()
    
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first()
    if not dataset:
        return jsonify({'message': '数据集不存在或无权限访问'}), 404
    
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, dataset.filename)
        
        if not os.path.exists(file_path):
            return jsonify({'message': '数据文件不存在'}), 404
        
        # 读取前几行数据作为预览
        import pandas as pd
        
        if dataset.file_type == 'csv':
            df = pd.read_csv(file_path, nrows=10)
        elif dataset.file_type == 'json':
            df = pd.read_json(file_path, nrows=10)
        elif dataset.file_type in ['xlsx', 'xls']:
            df = pd.read_excel(file_path, nrows=10)
        else:
            return jsonify({'message': '不支持的文件格式'}), 400
        
        preview_data = {
            'columns': df.columns.tolist(),
            'data': df.to_dict('records'),
            'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'shape': df.shape,
            'total_records': dataset.record_count or 'Unknown'
        }
        
        return jsonify({
            'dataset_info': dataset.to_dict(),
            'preview': preview_data
        }), 200
        
    except Exception as e:
        return jsonify({'message': '预览失败'}), 500


@api_bp.route('/datasets/statistics', methods=['GET'])
@jwt_required()
def get_datasets_statistics():
    """获取数据集统计信息"""
    user_id = get_jwt_identity()
    
    try:
        # 用户数据集统计
        user_datasets = Dataset.query.filter_by(user_id=user_id)
        total_datasets = user_datasets.count()
        valid_datasets = user_datasets.filter_by(is_valid=True).count()
        
        # 文件类型统计
        type_stats = {}
        for file_type in ['csv', 'json', 'xlsx', 'xls']:
            count = user_datasets.filter_by(file_type=file_type).count()
            if count > 0:
                type_stats[file_type] = count
        
        # 数据格式统计
        format_stats = {}
        for data_format in ['BLTE', 'Transaction', 'Generic']:
            count = user_datasets.filter_by(data_format=data_format).count()
            if count > 0:
                format_stats[data_format] = count
        
        # 总文件大小
        total_size = db.session.query(db.func.sum(Dataset.file_size)).filter_by(user_id=user_id).scalar() or 0
        
        # 最新上传的数据集
        latest_datasets = user_datasets.order_by(Dataset.upload_time.desc()).limit(5).all()
        
        return jsonify({
            'total_datasets': total_datasets,
            'valid_datasets': valid_datasets,
            'invalid_datasets': total_datasets - valid_datasets,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_type_stats': type_stats,
            'data_format_stats': format_stats,
            'latest_datasets': [dataset.to_dict() for dataset in latest_datasets]
        }), 200
        
    except Exception as e:
        return jsonify({'message': '获取统计信息失败'}), 500