"""
认证API路由
"""
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from . import api_bp
from ..models.user import User
from .. import db


@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    # 验证必填字段
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    # 查找用户
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    if not user.is_active:
        return jsonify({'message': '用户账户已被禁用'}), 403
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # 生成JWT token
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 验证必填字段
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': '用户名和密码不能为空'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': '用户名已存在'}), 409
    
    # 检查邮箱是否已存在
    if data.get('email') and User.query.filter_by(email=data['email']).first():
        return jsonify({'message': '邮箱已存在'}), 409
    
    try:
        # 创建新用户
        user = User(
            username=data['username'],
            email=data.get('email')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': '注册成功',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': '注册失败，请稍后重试'}), 500


@api_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户信息"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@api_bp.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户信息"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    data = request.get_json()
    
    try:
        # 更新邮箱
        if 'email' in data:
            if data['email'] and User.query.filter(User.email == data['email'], User.id != user.id).first():
                return jsonify({'message': '邮箱已被使用'}), 409
            user.email = data['email']
        
        # 更新密码
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': '用户信息更新成功',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': '更新失败，请稍后重试'}), 500