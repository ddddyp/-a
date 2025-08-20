"""
任务服务 - 异步任务管理和调度
提供任务创建、执行、监控、取消等功能
"""
import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue, Empty

from .algorithm_service import AlgorithmService


class TaskService:
    """任务服务 - 管理异步任务的执行和监控"""
    
    def __init__(self, max_concurrent_tasks: int = 3, algorithm_service: Optional[AlgorithmService] = None):
        """
        初始化任务服务
        
        Args:
            max_concurrent_tasks: 最大并发任务数
            algorithm_service: 算法服务实例
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.algorithm_service = algorithm_service or AlgorithmService(use_optimized_features=True)
        
        # 线程池执行器
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        
        # 任务队列和状态管理
        self.task_queue = Queue()
        self.running_tasks: Dict[int, Future] = {}
        self.task_results: Dict[int, Any] = {}
        
        # 任务统计
        self.total_tasks_created = 0
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0
        
        # 线程锁
        self._lock = threading.Lock()
    
    def create_task(self, name: str, description: str, algorithm_name: str,
                   dataset_id: int, user_id: int, 
                   parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建新任务（需要数据库模型支持）
        
        Args:
            name: 任务名称
            description: 任务描述
            algorithm_name: 算法名称
            dataset_id: 数据集ID
            user_id: 用户ID
            parameters: 算法参数
            
        Returns:
            Dict: 任务信息
        """
        try:
            # 这里应该创建数据库记录，暂时返回模拟数据
            task_info = {
                'id': self._generate_task_id(),
                'name': name,
                'description': description,
                'algorithm_name': algorithm_name,
                'dataset_id': dataset_id,
                'user_id': user_id,
                'parameters': parameters or {},
                'status': 'pending',
                'progress': 0,
                'current_stage': '等待执行',
                'created_at': datetime.utcnow(),
                'started_at': None,
                'completed_at': None,
                'processing_time': None,
                'error_message': None
            }
            
            with self._lock:
                self.total_tasks_created += 1
            
            return task_info
            
        except Exception as e:
            raise Exception(f"任务创建失败: {str(e)}")
    
    def start_task(self, task_id: int, dataset_path: str) -> bool:
        """
        启动任务执行
        
        Args:
            task_id: 任务ID
            dataset_path: 数据集文件路径
            
        Returns:
            bool: 是否启动成功
        """
        try:
            # 检查并发限制
            with self._lock:
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    return False
            
            # 获取任务信息（这里应该从数据库获取）
            task_info = self._get_task_info(task_id)
            if not task_info or task_info['status'] != 'pending':
                return False
            
            # 更新任务状态为运行中
            self._update_task_status(task_id, 'running', started_at=datetime.utcnow())
            
            # 提交到线程池异步执行
            future = self.executor.submit(
                self._execute_task,
                task_id,
                task_info['algorithm_name'],
                dataset_path,
                task_info['parameters']
            )
            
            # 记录运行中的任务
            with self._lock:
                self.running_tasks[task_id] = future
            
            # 设置完成回调
            future.add_done_callback(lambda f: self._task_completed_callback(task_id, f))
            
            return True
            
        except Exception as e:
            self._mark_task_failed(task_id, f"任务启动失败: {str(e)}")
            return False
    
    def _execute_task(self, task_id: int, algorithm_name: str, 
                     dataset_path: str, parameters: Dict[str, Any]):
        """
        执行任务的内部方法
        
        Args:
            task_id: 任务ID
            algorithm_name: 算法名称
            dataset_path: 数据集路径
            parameters: 算法参数
        """
        try:
            # 执行算法
            start_time = time.time()
            
            result = self.algorithm_service.run_algorithm(
                algorithm_name=algorithm_name,
                dataset_path=dataset_path,
                parameters=parameters,
                task_id=task_id
            )
            
            processing_time = time.time() - start_time
            
            # 保存结果
            self._save_task_result(task_id, result)
            
            # 标记任务完成
            self._mark_task_completed(task_id, processing_time)
            
            return result
            
        except Exception as e:
            # 标记任务失败
            self._mark_task_failed(task_id, str(e))
            raise e
    
    def _task_completed_callback(self, task_id: int, future: Future):
        """
        任务完成回调函数
        
        Args:
            task_id: 任务ID
            future: Future对象
        """
        with self._lock:
            # 从运行中任务列表移除
            self.running_tasks.pop(task_id, None)
            
            # 更新统计信息
            if future.exception():
                self.total_tasks_failed += 1
            else:
                self.total_tasks_completed += 1
    
    def cancel_task(self, task_id: int) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否取消成功
        """
        with self._lock:
            future = self.running_tasks.get(task_id)
            if future and not future.done():
                # 尝试取消任务
                if future.cancel():
                    self.running_tasks.pop(task_id, None)
                    self._update_task_status(task_id, 'cancelled')
                    return True
        
        return False
    
    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict]: 任务状态信息
        """
        # 这里应该从数据库获取任务信息
        task_info = self._get_task_info(task_id)
        
        if task_info:
            # 添加运行时状态
            with self._lock:
                is_running = task_id in self.running_tasks
                
            task_info['is_running'] = is_running
            task_info['queue_position'] = self._get_queue_position(task_id)
            
        return task_info
    
    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """
        获取当前运行中的任务列表
        
        Returns:
            List[Dict]: 运行中的任务信息列表
        """
        with self._lock:
            running_task_ids = list(self.running_tasks.keys())
        
        running_tasks = []
        for task_id in running_task_ids:
            task_info = self._get_task_info(task_id)
            if task_info:
                running_tasks.append(task_info)
        
        return running_tasks
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """
        获取任务服务统计信息
        
        Returns:
            Dict: 统计信息
        """
        with self._lock:
            stats = {
                'total_tasks_created': self.total_tasks_created,
                'total_tasks_completed': self.total_tasks_completed,
                'total_tasks_failed': self.total_tasks_failed,
                'current_running_tasks': len(self.running_tasks),
                'max_concurrent_tasks': self.max_concurrent_tasks,
                'success_rate': (self.total_tasks_completed / max(self.total_tasks_created, 1)) * 100,
                'queue_size': self.task_queue.qsize(),
                'executor_alive': not self.executor._shutdown
            }
        
        return stats
    
    def cleanup_completed_tasks(self, hours: int = 24):
        """
        清理完成的任务结果（超过指定时间）
        
        Args:
            hours: 保留时间（小时）
        """
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        
        with self._lock:
            # 清理任务结果缓存
            expired_tasks = []
            for task_id, result in self.task_results.items():
                if result.get('completed_at', 0) < cutoff_time:
                    expired_tasks.append(task_id)
            
            for task_id in expired_tasks:
                self.task_results.pop(task_id, None)
    
    def shutdown(self, wait: bool = True):
        """
        关闭任务服务
        
        Args:
            wait: 是否等待正在运行的任务完成
        """
        self.executor.shutdown(wait=wait)
        
        with self._lock:
            self.running_tasks.clear()
            self.task_results.clear()
    
    # 私有辅助方法
    
    def _generate_task_id(self) -> int:
        """生成任务ID（简单实现）"""
        return int(time.time() * 1000) % 1000000
    
    def _get_task_info(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        获取任务信息（模拟数据库查询）
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict]: 任务信息
        """
        # 这里应该从数据库查询任务信息
        # 目前返回模拟数据
        return {
            'id': task_id,
            'name': f'任务-{task_id}',
            'status': 'pending',
            'progress': 0,
            'current_stage': '等待执行',
            'algorithm_name': 'DBSCAN',
            'parameters': {},
            'created_at': datetime.utcnow(),
            'started_at': None,
            'completed_at': None,
            'error_message': None
        }
    
    def _update_task_status(self, task_id: int, status: str, **kwargs):
        """
        更新任务状态（模拟数据库更新）
        
        Args:
            task_id: 任务ID
            status: 新状态
            **kwargs: 其他要更新的字段
        """
        # 这里应该更新数据库记录
        pass
    
    def _save_task_result(self, task_id: int, result: Dict[str, Any]):
        """
        保存任务结果（模拟数据库保存）
        
        Args:
            task_id: 任务ID
            result: 算法结果
        """
        # 这里应该将结果保存到数据库
        with self._lock:
            self.task_results[task_id] = {
                'result': result,
                'completed_at': datetime.utcnow().timestamp()
            }
    
    def _mark_task_completed(self, task_id: int, processing_time: float):
        """
        标记任务完成
        
        Args:
            task_id: 任务ID
            processing_time: 处理时间
        """
        self._update_task_status(
            task_id,
            'completed',
            completed_at=datetime.utcnow(),
            processing_time=processing_time,
            progress=100,
            current_stage='分析完成'
        )
    
    def _mark_task_failed(self, task_id: int, error_message: str):
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
        """
        self._update_task_status(
            task_id,
            'failed',
            completed_at=datetime.utcnow(),
            error_message=error_message,
            current_stage='执行失败'
        )
    
    def _get_queue_position(self, task_id: int) -> int:
        """
        获取任务在队列中的位置
        
        Args:
            task_id: 任务ID
            
        Returns:
            int: 队列位置（0表示不在队列中）
        """
        # 简单实现，实际应该根据任务创建时间排序
        return 0