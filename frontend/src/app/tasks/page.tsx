'use client';

import React, { useState, useEffect } from 'react';
import { 
  Table, Card, Tag, Button, Space, Popconfirm, 
  message, Progress, Tooltip, Row, Col, Statistic,
  Modal, Descriptions, Alert 
} from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import ProtectedRoute from '@/components/ProtectedRoute';
import MainLayout from '@/components/Layout/MainLayout';
import apiClient, { Task } from '@/lib/api';
import type { ColumnsType } from 'antd/es/table';

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [statistics, setStatistics] = useState<any>(null);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchTasks();
    fetchStatistics();
    
    // 设置自动刷新
    const interval = setInterval(() => {
      fetchTasks();
    }, 5000); // 每5秒刷新一次
    
    setRefreshInterval(interval);
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await apiClient.getTasks();
      setTasks(response.tasks || []);
    } catch (error: any) {
      message.error('获取任务列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await apiClient.getTaskStatistics();
      setStatistics(response);
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  const handleStartTask = async (taskId: number) => {
    try {
      await apiClient.startTask(taskId);
      message.success('任务启动成功');
      fetchTasks();
    } catch (error: any) {
      message.error(error?.response?.data?.message || '启动任务失败');
    }
  };

  const handleCancelTask = async (taskId: number) => {
    try {
      await apiClient.cancelTask(taskId);
      message.success('任务取消成功');
      fetchTasks();
    } catch (error: any) {
      message.error('取消任务失败');
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    try {
      await apiClient.deleteTask(taskId);
      message.success('删除成功');
      fetchTasks();
      fetchStatistics();
    } catch (error: any) {
      message.error('删除失败');
    }
  };

  const handleViewDetails = async (task: Task) => {
    try {
      const response = await apiClient.getTask(task.id);
      setSelectedTask(response.task);
      setDetailModalVisible(true);
    } catch (error) {
      message.error('获取任务详情失败');
    }
  };

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { color: string; text: string; icon: React.ReactNode }> = {
      'pending': { 
        color: 'orange', 
        text: '待处理', 
        icon: <ClockCircleOutlined /> 
      },
      'running': { 
        color: 'green', 
        text: '运行中', 
        icon: <PlayCircleOutlined /> 
      },
      'completed': { 
        color: 'blue', 
        text: '已完成', 
        icon: <CheckCircleOutlined /> 
      },
      'failed': { 
        color: 'red', 
        text: '失败', 
        icon: <ExclamationCircleOutlined /> 
      },
      'cancelled': { 
        color: 'default', 
        text: '已取消', 
        icon: <PauseCircleOutlined /> 
      }
    };
    return configs[status] || { color: 'default', text: status, icon: null };
  };

  const getAlgorithmColor = (algorithm: string): string => {
    const colors: Record<string, string> = {
      'DBSCAN': 'blue',
      'IsolationForest': 'green',
      'KmeansPlus': 'orange'
    };
    return colors[algorithm] || 'default';
  };

  const columns: ColumnsType<Task> = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '算法',
      dataIndex: 'algorithm_name',
      key: 'algorithm_name',
      width: 120,
      render: (algorithm: string) => (
        <Tag color={getAlgorithmColor(algorithm)}>{algorithm}</Tag>
      ),
    },
    {
      title: '数据集',
      key: 'dataset',
      width: 150,
      ellipsis: true,
      render: (_, record) => record.dataset?.name || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config = getStatusConfig(status);
        return (
          <Tag icon={config.icon} color={config.color}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (progress: number, record) => (
        <div>
          <Progress 
            percent={progress} 
            size="small" 
            status={record.status === 'failed' ? 'exception' : 'active'}
          />
          {record.current_stage && (
            <div className="text-xs text-gray-500 mt-1">
              {record.current_stage}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '处理时间',
      dataIndex: 'processing_time',
      key: 'processing_time',
      width: 100,
      render: (time: number) => 
        time ? `${time.toFixed(2)}s` : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetails(record)}
            />
          </Tooltip>
          
          {record.status === 'pending' && (
            <Tooltip title="启动任务">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                onClick={() => handleStartTask(record.id)}
              />
            </Tooltip>
          )}
          
          {record.status === 'running' && (
            <Popconfirm
              title="确定取消此任务吗？"
              onConfirm={() => handleCancelTask(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Tooltip title="取消任务">
                <Button
                  type="text"
                  icon={<PauseCircleOutlined />}
                />
              </Tooltip>
            </Popconfirm>
          )}
          
          {['completed', 'failed', 'cancelled'].includes(record.status) && (
            <Popconfirm
              title="确定删除此任务吗？"
              description="删除后无法恢复，相关结果也会被删除。"
              onConfirm={() => handleDeleteTask(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Tooltip title="删除任务">
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <ProtectedRoute>
      <MainLayout>
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-800">任务监控</h1>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                fetchTasks();
                fetchStatistics();
              }}
            >
              刷新
            </Button>
          </div>

          {/* 统计卡片 */}
          {statistics && (
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={6}>
                <Card>
                  <Statistic
                    title="任务总数"
                    value={statistics.total_tasks || 0}
                    suffix="个"
                  />
                </Card>
              </Col>
              <Col xs={24} sm={6}>
                <Card>
                  <Statistic
                    title="成功率"
                    value={statistics.success_rate || 0}
                    suffix="%"
                    precision={1}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={6}>
                <Card>
                  <Statistic
                    title="平均处理时间"
                    value={statistics.avg_processing_time || 0}
                    suffix="s"
                    precision={2}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={6}>
                <Card>
                  <Statistic
                    title="运行中任务"
                    value={tasks.filter(t => t.status === 'running').length}
                    suffix="个"
                  />
                </Card>
              </Col>
            </Row>
          )}

          {/* 任务表格 */}
          <Card>
            <Table
              columns={columns}
              dataSource={tasks}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) =>
                  `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              }}
              scroll={{ x: 1200 }}
            />
          </Card>

          {/* 任务详情模态框 */}
          <Modal
            title="任务详情"
            open={detailModalVisible}
            onCancel={() => setDetailModalVisible(false)}
            footer={[
              <Button key="close" onClick={() => setDetailModalVisible(false)}>
                关闭
              </Button>
            ]}
            width={800}
          >
            {selectedTask && (
              <div className="space-y-4">
                {/* 基本信息 */}
                <Descriptions title="基本信息" bordered size="small">
                  <Descriptions.Item label="任务名称" span={2}>
                    {selectedTask.name}
                  </Descriptions.Item>
                  <Descriptions.Item label="算法">
                    <Tag color={getAlgorithmColor(selectedTask.algorithm_name)}>
                      {selectedTask.algorithm_name}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="状态" span={2}>
                    {(() => {
                      const config = getStatusConfig(selectedTask.status);
                      return (
                        <Tag icon={config.icon} color={config.color}>
                          {config.text}
                        </Tag>
                      );
                    })()}
                  </Descriptions.Item>
                  <Descriptions.Item label="进度">
                    {selectedTask.progress}%
                  </Descriptions.Item>
                  <Descriptions.Item label="描述" span={3}>
                    {selectedTask.description || '无'}
                  </Descriptions.Item>
                </Descriptions>

                {/* 数据集信息 */}
                {selectedTask.dataset && (
                  <Descriptions title="数据集信息" bordered size="small">
                    <Descriptions.Item label="数据集名称" span={2}>
                      {selectedTask.dataset.name}
                    </Descriptions.Item>
                    <Descriptions.Item label="文件类型">
                      {selectedTask.dataset.file_type?.toUpperCase()}
                    </Descriptions.Item>
                    <Descriptions.Item label="记录数" span={2}>
                      {selectedTask.dataset.record_count?.toLocaleString() || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="列数">
                      {selectedTask.dataset.column_count || '-'}
                    </Descriptions.Item>
                  </Descriptions>
                )}

                {/* 时间信息 */}
                <Descriptions title="时间信息" bordered size="small">
                  <Descriptions.Item label="创建时间" span={2}>
                    {new Date(selectedTask.created_at).toLocaleString()}
                  </Descriptions.Item>
                  <Descriptions.Item label="开始时间">
                    {selectedTask.started_at 
                      ? new Date(selectedTask.started_at).toLocaleString() 
                      : '-'
                    }
                  </Descriptions.Item>
                  <Descriptions.Item label="完成时间" span={2}>
                    {selectedTask.completed_at 
                      ? new Date(selectedTask.completed_at).toLocaleString() 
                      : '-'
                    }
                  </Descriptions.Item>
                  <Descriptions.Item label="处理时间">
                    {selectedTask.processing_time 
                      ? `${selectedTask.processing_time.toFixed(2)}s` 
                      : '-'
                    }
                  </Descriptions.Item>
                </Descriptions>

                {/* 参数配置 */}
                {selectedTask.parameters && (
                  <div>
                    <h4 className="font-semibold mb-2">算法参数</h4>
                    <div className="bg-gray-50 p-3 rounded">
                      <pre className="text-sm">
                        {JSON.stringify(selectedTask.parameters, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* 错误信息 */}
                {selectedTask.error_message && (
                  <Alert
                    message="错误信息"
                    description={selectedTask.error_message}
                    type="error"
                    showIcon
                  />
                )}

                {/* 当前阶段 */}
                {selectedTask.current_stage && selectedTask.status === 'running' && (
                  <Alert
                    message="当前阶段"
                    description={selectedTask.current_stage}
                    type="info"
                    showIcon
                  />
                )}

                {/* 结果信息 */}
                {selectedTask.latest_result && (
                  <div>
                    <h4 className="font-semibold mb-2">最新结果</h4>
                    <Descriptions bordered size="small">
                      <Descriptions.Item label="轮廓系数">
                        {selectedTask.latest_result.silhouette_score?.toFixed(3) || '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="检测率">
                        {selectedTask.latest_result.bot_addresses_pct?.toFixed(1)}%
                      </Descriptions.Item>
                      <Descriptions.Item label="聚类数量">
                        {selectedTask.latest_result.clusters_count || '-'}
                      </Descriptions.Item>
                    </Descriptions>
                  </div>
                )}
              </div>
            )}
          </Modal>
        </div>
      </MainLayout>
    </ProtectedRoute>
  );
}