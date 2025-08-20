"""
数据服务 - 数据集管理和处理
提供数据集上传、验证、管理等功能
"""
import os
import hashlib
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from werkzeug.utils import secure_filename
from datetime import datetime


class DataService:
    """数据服务 - 管理数据集相关操作"""
    
    def __init__(self, upload_folder: str, max_file_size: int = 100 * 1024 * 1024):
        """
        初始化数据服务
        
        Args:
            upload_folder: 文件上传目录
            max_file_size: 最大文件大小（字节，默认100MB）
        """
        self.upload_folder = upload_folder
        self.max_file_size = max_file_size
        self.allowed_extensions = {'csv', 'json', 'xlsx', 'xls'}
        
        # 确保上传目录存在
        os.makedirs(upload_folder, exist_ok=True)
    
    def validate_file(self, file) -> Tuple[bool, Optional[str]]:
        """
        验证上传文件
        
        Args:
            file: 上传的文件对象
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        # 检查文件是否存在
        if not file or not file.filename:
            return False, "未选择文件"
        
        # 检查文件扩展名
        if not self._allowed_file(file.filename):
            return False, f"不支持的文件格式，支持的格式: {', '.join(self.allowed_extensions)}"
        
        # 检查文件大小（如果可以获取）
        try:
            file.seek(0, 2)  # 移动到文件末尾
            file_size = file.tell()
            file.seek(0)  # 重置到开头
            
            if file_size > self.max_file_size:
                return False, f"文件过大，最大支持 {self.max_file_size // (1024*1024)}MB"
        except Exception:
            # 某些文件对象可能不支持 seek
            pass
        
        return True, None
    
    def save_file(self, file, user_id: int) -> Dict[str, Any]:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件对象
            user_id: 用户ID
            
        Returns:
            Dict: 保存的文件信息
            
        Raises:
            ValueError: 文件验证失败
            Exception: 文件保存失败
        """
        # 验证文件
        is_valid, error_msg = self.validate_file(file)
        if not is_valid:
            raise ValueError(error_msg)
        
        try:
            # 生成安全的文件名
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(f"{user_id}_{timestamp}_{original_filename}".encode()).hexdigest()[:8]
            filename = f"{user_id}_{timestamp}_{file_hash}.{file_extension}"
            
            # 保存文件
            file_path = os.path.join(self.upload_folder, filename)
            file.save(file_path)
            
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            
            # 验证文件内容
            validation_info = self._validate_file_content(file_path, file_extension)
            
            return {
                'original_filename': original_filename,
                'filename': filename,
                'file_path': file_path,
                'file_type': file_extension,
                'file_size': file_size,
                'validation_info': validation_info,
                'is_valid': validation_info.get('is_valid', True),
                'upload_time': datetime.utcnow()
            }
            
        except Exception as e:
            # 如果保存失败，清理可能创建的文件
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            raise e
    
    def _allowed_file(self, filename: str) -> bool:
        """
        检查文件扩展名是否允许
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否允许
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _validate_file_content(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        验证文件内容格式
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            Dict: 验证结果信息
        """
        validation_info = {
            'is_valid': True,
            'error_message': None,
            'record_count': 0,
            'column_count': 0,
            'data_format': 'Unknown',
            'columns': [],
            'sample_data': {}
        }
        
        try:
            # 根据文件类型读取数据
            if file_type == 'csv':
                df = pd.read_csv(file_path)
            elif file_type == 'json':
                df = pd.read_json(file_path)
            elif file_type in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                validation_info['is_valid'] = False
                validation_info['error_message'] = f"不支持的文件类型: {file_type}"
                return validation_info
            
            # 基本信息
            validation_info['record_count'] = len(df)
            validation_info['column_count'] = len(df.columns)
            validation_info['columns'] = df.columns.tolist()
            
            # 检查数据是否为空
            if df.empty:
                validation_info['is_valid'] = False
                validation_info['error_message'] = "文件内容为空"
                return validation_info
            
            # 检测数据格式
            data_format = self._detect_data_format(df)
            validation_info['data_format'] = data_format
            
            # 生成样本数据
            validation_info['sample_data'] = df.head(3).to_dict('records')
            
            # 数据质量检查
            quality_info = self._check_data_quality(df)
            validation_info.update(quality_info)
            
        except pd.errors.EmptyDataError:
            validation_info['is_valid'] = False
            validation_info['error_message'] = "文件内容为空或格式错误"
        except pd.errors.ParserError as e:
            validation_info['is_valid'] = False
            validation_info['error_message'] = f"文件解析错误: {str(e)}"
        except Exception as e:
            validation_info['is_valid'] = False
            validation_info['error_message'] = f"文件验证失败: {str(e)}"
        
        return validation_info
    
    def _detect_data_format(self, df: pd.DataFrame) -> str:
        """
        检测数据格式类型
        
        Args:
            df: 数据框
            
        Returns:
            str: 数据格式类型
        """
        columns = df.columns.tolist()
        
        # 检测BLTE格式 (区块链聚合特征)
        blte_indicators = ['in_degree', 'out_degree', 'unique_out_degree', 'total_ether_received']
        if any(indicator in columns for indicator in blte_indicators):
            return 'BLTE'
        
        # 检测Transaction格式 (原始交易记录)
        transaction_indicators = ['from', 'to', 'value', 'timestamp', 'hash']
        if any(indicator in columns for indicator in transaction_indicators):
            return 'Transaction'
        
        # 检测通用数值格式
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) >= len(columns) * 0.7:  # 70%以上为数值列
            return 'Generic'
        
        return 'Unknown'
    
    def _check_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        检查数据质量
        
        Args:
            df: 数据框
            
        Returns:
            Dict: 数据质量信息
        """
        quality_info = {
            'missing_values': {},
            'duplicate_records': 0,
            'numeric_columns': [],
            'non_numeric_columns': [],
            'data_types': {},
            'warnings': []
        }
        
        try:
            # 缺失值检查
            missing = df.isnull().sum()
            quality_info['missing_values'] = {col: int(count) for col, count in missing.items() if count > 0}
            
            # 重复记录检查
            quality_info['duplicate_records'] = int(df.duplicated().sum())
            
            # 数据类型分析
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()
            
            quality_info['numeric_columns'] = numeric_cols
            quality_info['non_numeric_columns'] = non_numeric_cols
            quality_info['data_types'] = {col: str(dtype) for col, dtype in df.dtypes.items()}
            
            # 生成警告
            warnings = []
            
            # 缺失值警告
            if quality_info['missing_values']:
                warnings.append(f"发现缺失值: {list(quality_info['missing_values'].keys())}")
            
            # 重复记录警告
            if quality_info['duplicate_records'] > 0:
                warnings.append(f"发现 {quality_info['duplicate_records']} 条重复记录")
            
            # 数值列比例警告
            if len(numeric_cols) < len(df.columns) * 0.5:
                warnings.append("数值列比例较低，可能影响算法效果")
            
            # 样本数量警告
            if len(df) < 100:
                warnings.append("样本数量较少，建议至少100条记录以获得稳定结果")
            elif len(df) > 100000:
                warnings.append("样本数量较大，处理时间可能较长")
            
            quality_info['warnings'] = warnings
            
        except Exception as e:
            quality_info['warnings'] = [f"数据质量检查失败: {str(e)}"]
        
        return quality_info
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            filename: 文件名
            
        Returns:
            Optional[Dict]: 文件信息，如果文件不存在返回None
        """
        file_path = os.path.join(self.upload_folder, filename)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            stat = os.stat(file_path)
            return {
                'filename': filename,
                'file_path': file_path,
                'file_size': stat.st_size,
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime)
            }
        except Exception:
            return None
    
    def delete_file(self, filename: str) -> bool:
        """
        删除文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否删除成功
        """
        file_path = os.path.join(self.upload_folder, filename)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def get_upload_statistics(self) -> Dict[str, Any]:
        """
        获取上传统计信息
        
        Returns:
            Dict: 统计信息
        """
        try:
            files = os.listdir(self.upload_folder)
            total_files = len(files)
            total_size = sum(os.path.getsize(os.path.join(self.upload_folder, f)) for f in files)
            
            # 按类型统计
            type_stats = {}
            for filename in files:
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'unknown'
                type_stats[ext] = type_stats.get(ext, 0) + 1
            
            return {
                'total_files': total_files,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_types': type_stats,
                'upload_folder': self.upload_folder
            }
        except Exception:
            return {
                'total_files': 0,
                'total_size': 0,
                'total_size_mb': 0,
                'file_types': {},
                'upload_folder': self.upload_folder
            }