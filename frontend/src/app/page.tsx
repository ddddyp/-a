'use client';

import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Table, Tag, Spin, Alert } from 'antd';
import { 
  DatabaseOutlined, 
  ExperimentOutlined, 
  BarChartOutlined,
  ClockCircleOutlined 
} from '@ant-design/icons';
import dynamic from 'next/dynamic';

const ReactECharts = dynamic(
  () => import('echarts-for-react'),
  { ssr: false }
);
import ProtectedRoute from '@/components/ProtectedRoute';
import MainLayout from '@/components/Layout/MainLayout';
import apiClient, { Task, Result } from '@/lib/api';
import type { ColumnsType } from 'antd/es/table';

interface DashboardData {
  totalDatasets: number;
  totalTasks: number;
  totalResults: number;
  runningTasks: number;
  recentTasks: Task[];
  recentResults: Result[];
  algorithmStats: Record<string, number>;
  statusStats: Record<string, number>;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // 并行获取所有数据
      const [
        datasetsResponse,
        tasksResponse,
        resultsResponse,
        runningTasksResponse,
        taskStatsResponse,
        resultStatsResponse
      ] = await Promise.all([
        apiClient.getDatasetStatistics(),
        apiClient.getTasks(),
        apiClient.getResults(),
        apiClient.getRunningTasks(),
        apiClient.getTaskStatistics(),
        apiClient.getResultStatistics()
      ]);

      setData({
        totalDatasets: datasetsResponse.total_datasets || 0,
        totalTasks: taskStatsResponse.total_tasks || 0,
        totalResults: resultStatsResponse.total_results || 0,
        runningTasks: runningTasksResponse.count || 0,
        recentTasks: tasksResponse.tasks?.slice(0, 5) || [],
        recentResults: resultsResponse.results?.slice(0, 5) || [],
        algorithmStats: taskStatsResponse.algorithm_stats || {},
        statusStats: taskStatsResponse.status_stats || {}
      });
      
      setError(null);
    } catch (err: any) {
      setError('获取仪表板数据失败');
      console.error('Dashboard data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // 任务状态分布图表配置（饼图）
  const getTaskStatusPieChartOption = () => {
    const statuses = Object.keys(data?.statusStats || {});
    const values = Object.values(data?.statusStats || {});
    
    return {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      series: [
        {
          type: 'pie',
          radius: ['50%', '80%'],
          center: ['50%', '50%'],
          data: statuses.map((status, index) => {
            const statusMap: Record<string, { name: string; color: string }> = {
              'pending': { name: '待处理', color: '#faad14' },
              'running': { name: '运行中', color: '#52c41a' },
              'completed': { name: '已完成', color: '#52c41a' },
              'failed': { name: '失败', color: '#ff4d4f' },
              'cancelled': { name: '已取消', color: '#d9d9d9' }
            };
            const config = statusMap[status] || { name: status, color: '#52c41a' };
            return {
              value: values[index],
              name: config.name,
              itemStyle: {
                color: config.color
              }
            };
          }),
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          label: {
            show: false
          }
        }
      ]
    };
  };

  // 检测结果趋势图表配置（柱状图）
  const getDetectionTrendChartOption = () => {
    // 模拟检测结果趋势数据
    const categories = ['9', '8', '7', '6', '5'];
    const normalData = [18000, 19000, 20000, 4500, 5000];
    const botData = [2500, 1500, 1000, 500, 300];
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        }
      },
      yAxis: {
        type: 'value',
        max: 25000,
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0'
          }
        }
      },
      series: [
        {
          name: '机器人交易',
          type: 'bar',
          stack: 'total',
          data: botData,
          itemStyle: {
            color: '#ff4d4f'
          },
          barMaxWidth: 40
        },
        {
          name: '正常交易',
          type: 'bar',
          stack: 'total',
          data: normalData,
          itemStyle: {
            color: '#52c41a'
          },
          barMaxWidth: 40
        }
      ]
    };
  };

  // 最近任务表格列配置
  const taskColumns: ColumnsType<Task> = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '算法',
      dataIndex: 'algorithm_name',
      key: 'algorithm_name',
      render: (algorithm: string) => (
        <Tag color="blue">{algorithm}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig: Record<string, { color: string; text: string }> = {
          'pending': { color: 'orange', text: '待处理' },
          'running': { color: 'green', text: '运行中' },
          'completed': { color: 'blue', text: '已完成' },
          'failed': { color: 'red', text: '失败' },
          'cancelled': { color: 'default', text: '已取消' }
        };
        const config = statusConfig[status] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number) => `${progress}%`,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
  ];

  if (loading) {
    return (
      <ProtectedRoute>
        <MainLayout>
          <div className="flex items-center justify-center min-h-[400px]">
            <Spin size="large" />
          </div>
        </MainLayout>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <MainLayout>
        <div className="space-y-6 bg-white min-h-screen -m-6 p-6">
          <h1 className="text-2xl font-bold text-gray-800">仪表板</h1>
          
          {error && (
            <Alert
              message="错误"
              description={error}
              type="error"
              showIcon
              closable
            />
          )}

          {/* 统计卡片 */}
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <Card className="stats-card-new stats-card-blue">
                <div className="stats-icon">
                  <DatabaseOutlined />
                </div>
                <div className="stats-content">
                  <div className="stats-number">{data?.totalDatasets || 3}</div>
                  <div className="stats-label">数据集总数</div>
                </div>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="stats-card-new stats-card-green">
                <div className="stats-icon">
                  <ExperimentOutlined />
                </div>
                <div className="stats-content">
                  <div className="stats-number">{data?.totalTasks || 9}</div>
                  <div className="stats-label">分析任务</div>
                </div>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="stats-card-new stats-card-orange">
                <div className="stats-icon">
                  <BarChartOutlined />
                </div>
                <div className="stats-content">
                  <div className="stats-number">{data?.totalResults || 9}</div>
                  <div className="stats-label">分析结果</div>
                </div>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="stats-card-new stats-card-purple">
                <div className="stats-icon">
                  <ClockCircleOutlined />
                </div>
                <div className="stats-content">
                  <div className="stats-number">100%</div>
                  <div className="stats-label">成功率</div>
                </div>
              </Card>
            </Col>
          </Row>

          {/* 图表区域 */}
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card className="chart-container">
                <div className="chart-header">
                  <h3 className="chart-title">任务状态分布</h3>
                </div>
                {data?.statusStats && Object.keys(data.statusStats).length > 0 ? (
                  <ReactECharts 
                    option={getTaskStatusPieChartOption()} 
                    style={{ height: '300px' }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-[300px] text-gray-500">
                    暂无数据
                  </div>
                )}
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card className="chart-container">
                <div className="chart-header">
                  <h3 className="chart-title">检测结果趋势</h3>
                </div>
                <ReactECharts 
                  option={getDetectionTrendChartOption()} 
                  style={{ height: '300px' }}
                />
              </Card>
            </Col>
          </Row>

          {/* 最近任务列表 */}
          <Card className="task-table-container">
            <div className="task-table-header">
              <h3 className="task-table-title">最近任务</h3>
              <span className="view-all-link">查看全部</span>
            </div>
            <Table
              columns={taskColumns}
              dataSource={data?.recentTasks || []}
              rowKey="id"
              pagination={false}
              size="small"
              scroll={{ x: 800 }}
              className="custom-table"
            />
          </Card>
        </div>
      </MainLayout>
    </ProtectedRoute>
  );
}