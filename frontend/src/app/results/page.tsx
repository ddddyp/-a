'use client';

import React, { useState, useEffect } from 'react';
import { 
  Table, Card, Tag, Button, Space, message, 
  Row, Col, Modal, Descriptions, Tooltip
} from 'antd';
import { 
  BarChartOutlined, 
  DownloadOutlined, 
  EyeOutlined,
  TrophyOutlined,
  ExperimentOutlined
} from '@ant-design/icons';
import dynamic from 'next/dynamic';

const ReactECharts = dynamic(
  () => import('echarts-for-react'),
  { ssr: false }
);
import ProtectedRoute from '@/components/ProtectedRoute';
import MainLayout from '@/components/Layout/MainLayout';
import apiClient, { Result } from '@/lib/api';
import type { ColumnsType } from 'antd/es/table';

export default function ResultsPage() {
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedResult, setSelectedResult] = useState<Result | null>(null);
  const [statistics, setStatistics] = useState<any>(null);

  useEffect(() => {
    fetchResults();
    fetchStatistics();
  }, []);

  const fetchResults = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getResults();
      setResults(response.results || []);
    } catch (error: any) {
      message.error('获取结果列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await apiClient.getResultStatistics();
      setStatistics(response);
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  const handleViewDetails = (result: Result) => {
    setSelectedResult(result);
    setDetailModalVisible(true);
  };

  const handleExport = async (resultId: number, format: string = 'csv') => {
    try {
      const blob = await apiClient.exportResult(resultId, format);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `result_${resultId}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
    }
  };



  const getQualityColor = (score: number): string => {
    if (score > 0.7) return 'success';
    if (score > 0.3) return 'processing';
    if (score > 0.1) return 'warning';
    return 'error';
  };

  const getQualityStatus = (score: number): string => {
    if (score > 0.7) return '优秀';
    if (score > 0.3) return '良好';
    if (score > 0.1) return '一般';
    return '较差';
  };

  const getDetectionRateColor = (rate: number): string => {
    if (rate >= 5 && rate <= 15) return 'success';
    if (rate >= 2 && rate <= 20) return 'warning';
    return 'error';
  };

  const getAlgorithmColor = (algorithm: string): string => {
    const colors: Record<string, string> = {
      'DBSCAN': 'blue',
      'IsolationForest': 'green',
      'KmeansPlus': 'orange'
    };
    return colors[algorithm] || 'default';
  };

  // 算法性能对比图表配置
  const getPerformanceChartOption = () => {
    const algorithmData: Record<string, { scores: number[]; rates: number[] }> = {};
    
    results.forEach(result => {
      if (!algorithmData[result.algorithm_name]) {
        algorithmData[result.algorithm_name] = { scores: [], rates: [] };
      }
      algorithmData[result.algorithm_name].scores.push(result.silhouette_score);
      algorithmData[result.algorithm_name].rates.push(result.bot_addresses_pct);
    });

    const algorithms = Object.keys(algorithmData);
    const avgScores = algorithms.map(alg => {
      const scores = algorithmData[alg].scores;
      return scores.reduce((sum, score) => sum + score, 0) / scores.length;
    });

    return {
      title: {
        text: '算法性能对比',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'category',
        data: algorithms
      },
      yAxis: {
        type: 'value',
        name: '平均轮廓系数',
        min: 0,
        max: 1
      },
      series: [
        {
          data: avgScores.map((score, index) => ({
            value: score,
            itemStyle: {
              color: ['#1890ff', '#52c41a', '#faad14'][index] || '#d9d9d9'
            }
          })),
          type: 'bar',
          showBackground: true,
          backgroundStyle: {
            color: 'rgba(180, 180, 180, 0.2)'
          }
        }
      ]
    };
  };

  // 检测状态分布图表配置（饼图）
  const getDetectionStatusChartOption = () => {
    // 计算检测状态统计
    const successCount = results.filter(r => r.silhouette_score > 0.3).length;
    const warningCount = results.filter(r => r.silhouette_score > 0.1 && r.silhouette_score <= 0.3).length;
    const errorCount = results.filter(r => r.silhouette_score <= 0.1).length;
    
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
          data: [
            {
              value: successCount,
              name: '检测成功',
              itemStyle: { color: '#52c41a' }
            },
            {
              value: warningCount,
              name: '检测警告',
              itemStyle: { color: '#faad14' }
            },
            {
              value: errorCount,
              name: '检测异常',
              itemStyle: { color: '#ff4d4f' }
            }
          ],
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

  // 机器人检测趋势图表配置（柱状图）
  const getBotDetectionTrendChartOption = () => {
    // 按时间分组统计机器人检测数据
    const trendData = results.slice(-10).map((result, index) => ({
      day: index + 1,
      bots: result.bot_addresses_count,
      normal: result.normal_addresses_count
    }));
    
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'category',
        data: trendData.map(d => d.day.toString()),
        axisLine: { show: false },
        axisTick: { show: false }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: {
          lineStyle: { color: '#f0f0f0' }
        }
      },
      series: [
        {
          name: '机器人地址',
          type: 'bar',
          stack: 'total',
          data: trendData.map(d => d.bots),
          itemStyle: { color: '#ff4d4f' },
          barMaxWidth: 40
        },
        {
          name: '正常地址',
          type: 'bar',
          stack: 'total',
          data: trendData.map(d => d.normal),
          itemStyle: { color: '#1890ff' },
          barMaxWidth: 40
        }
      ]
    };
  };

  // 算法性能对比分析图表配置（散点图）
  const getAlgorithmPerformanceScatterOption = () => {
    return {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const [rate, score, algorithm] = params.data;
          return `算法: ${algorithm}<br/>检测率: ${rate.toFixed(2)}%<br/>轮廓系数: ${score.toFixed(3)}`;
        }
      },
      xAxis: {
        type: 'value',
        name: '检测率 (%)',
        max: 1,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: '#f0f0f0' } }
      },
      yAxis: {
        type: 'value',
        name: '轮廓系数',
        max: 1,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: '#f0f0f0' } }
      },
      series: [
        {
          type: 'scatter',
          data: results.map(result => [
            result.bot_addresses_pct / 100,
            result.silhouette_score,
            result.algorithm_name
          ]),
          itemStyle: {
            color: '#1890ff'
          },
          symbolSize: 8
        }
      ]
    };
  };

  const columns: ColumnsType<Result> = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 80,
      sorter: (a, b) => a.task_id - b.task_id,
    },
    {
      title: '算法',
      dataIndex: 'algorithm_name',
      key: 'algorithm_name',
      width: 120,
      render: (algorithm: string) => (
        <Tag color={getAlgorithmColor(algorithm)}>{algorithm}</Tag>
      ),
      filters: [
        { text: 'DBSCAN', value: 'DBSCAN' },
        { text: 'IsolationForest', value: 'IsolationForest' },
        { text: 'KmeansPlus', value: 'KmeansPlus' },
      ],
      onFilter: (value, record) => record.algorithm_name === value,
    },
    {
      title: '聚类数量',
      dataIndex: 'clusters_count',
      key: 'clusters_count',
      width: 100,
      align: 'center',
      sorter: (a, b) => a.clusters_count - b.clusters_count,
    },
    {
      title: '检测效果',
      key: 'detection_effect',
      width: 160,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <div>
            <span className="text-xs text-gray-500">检测率: </span>
            <Tag color={getDetectionRateColor(record.bot_addresses_pct)}>
              {record.bot_addresses_pct.toFixed(1)}%
            </Tag>
          </div>
          <div>
            <span className="text-xs text-gray-500">质量: </span>
            <Tag color={getQualityColor(record.silhouette_score)}>
              {getQualityStatus(record.silhouette_score)}
            </Tag>
          </div>
        </Space>
      ),
    },
    {
      title: '轮廓系数',
      dataIndex: 'silhouette_score',
      key: 'silhouette_score',
      width: 100,
      align: 'center',
      render: (score: number) => (
        <Tooltip title={`质量评级: ${getQualityStatus(score)}`}>
          <span className={score > 0.3 ? 'text-green-600 font-semibold' : ''}>
            {score.toFixed(3)}
          </span>
        </Tooltip>
      ),
      sorter: (a, b) => a.silhouette_score - b.silhouette_score,
    },
    {
      title: '机器人数量',
      key: 'bot_count',
      width: 120,
      render: (_, record) => (
        <div>
          <div className="font-semibold">{record.bot_addresses_count.toLocaleString()}</div>
          <div className="text-xs text-gray-500">
            / {record.total_addresses.toLocaleString()}
          </div>
        </div>
      ),
    },
    {
      title: '处理时间',
      dataIndex: 'processing_time',
      key: 'processing_time',
      width: 100,
      align: 'center',
      render: (time: number) => `${time.toFixed(2)}s`,
      sorter: (a, b) => a.processing_time - b.processing_time,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => new Date(date).toLocaleString(),
      sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
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
          <Tooltip title="导出结果">
            <Button
              type="text"
              icon={<DownloadOutlined />}
              onClick={() => handleExport(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 计算总体统计
  const totalStats = results.length > 0 ? {
    totalResults: results.length,
    avgSilhouette: results.reduce((sum, r) => sum + r.silhouette_score, 0) / results.length,
    avgDetectionRate: results.reduce((sum, r) => sum + r.bot_addresses_pct, 0) / results.length,
    avgProcessingTime: results.reduce((sum, r) => sum + r.processing_time, 0) / results.length,
    bestResult: results.reduce((best, current) => 
      current.silhouette_score > best.silhouette_score ? current : best
    )
  } : null;

  return (
    <ProtectedRoute>
      <MainLayout>
        <div className="bg-white min-h-screen -m-6 p-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-6">结果展示</h1>

          {/* 统计概览 */}
          {totalStats && (
            <Row gutter={[16, 16]} className="mb-6">
              <Col xs={24} sm={6}>
                <Card className="stats-card-new stats-card-blue">
                  <div className="stats-icon">
                    <BarChartOutlined />
                  </div>
                  <div className="stats-content">
                    <div className="stats-number">{totalStats.totalResults}</div>
                    <div className="stats-label">分析任务总数</div>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={6}>
                <Card className="stats-card-new stats-card-red">
                  <div className="stats-icon">
                    <TrophyOutlined />
                  </div>
                  <div className="stats-content">
                    <div className="stats-number">
                      {results.reduce((sum, r) => sum + r.bot_addresses_count, 0).toLocaleString()}
                    </div>
                    <div className="stats-label">异常地址数</div>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={6}>
                <Card className="stats-card-new stats-card-orange">
                  <div className="stats-icon">
                    <ExperimentOutlined />
                  </div>
                  <div className="stats-content">
                    <div className="stats-number">{totalStats.avgDetectionRate.toFixed(3)}</div>
                    <div className="stats-label">平均检测率</div>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={6}>
                <Card className="stats-card-new stats-card-green">
                  <div className="stats-icon">
                    <TrophyOutlined />
                  </div>
                  <div className="stats-content">
                    <div className="stats-number">{totalStats.avgProcessingTime.toFixed(2)}秒</div>
                    <div className="stats-label">平均处理时间</div>
                  </div>
                </Card>
              </Col>
            </Row>
          )}

          {/* 图表展示 */}
          <Row gutter={[16, 16]} className="mb-6">
            <Col xs={24} lg={12}>
              <Card className="chart-container">
                <div className="chart-header">
                  <h3 className="chart-title">检测状态分布</h3>
                </div>
                {results.length > 0 ? (
                  <ReactECharts 
                    option={getDetectionStatusChartOption()} 
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
                  <h3 className="chart-title">机器人检测趋势</h3>
                </div>
                {results.length > 0 ? (
                  <ReactECharts 
                    option={getBotDetectionTrendChartOption()} 
                    style={{ height: '300px' }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-[300px] text-gray-500">
                    暂无数据
                  </div>
                )}
              </Card>
            </Col>
          </Row>

          {/* 算法性能对比分析 */}
          <Row gutter={[16, 16]} className="mb-6">
            <Col xs={24}>
              <Card className="chart-container">
                <div className="chart-header">
                  <h3 className="chart-title">算法性能对比分析</h3>
                </div>
                {results.length > 0 ? (
                  <ReactECharts 
                    option={getAlgorithmPerformanceScatterOption()} 
                    style={{ height: '400px' }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-[400px] text-gray-500">
                    暂无数据
                  </div>
                )}
              </Card>
            </Col>
          </Row>

          {/* 结果表格 */}
          <Card className="task-table-container">
            <div className="task-table-header">
              <h3 className="task-table-title">详细结果</h3>
            </div>
            <Table
              columns={columns}
              dataSource={results}
              rowKey="id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) =>
                  `共 ${total} 条数据`,
              }}
              scroll={{ x: 1200 }}
              className="custom-table"
            />
          </Card>

          {/* 结果详情模态框 */}
          <Modal
            title="结果详情"
            open={detailModalVisible}
            onCancel={() => setDetailModalVisible(false)}
            footer={[
              <Button key="export" onClick={() => selectedResult && handleExport(selectedResult.id)}>
                导出数据
              </Button>,
              <Button key="close" onClick={() => setDetailModalVisible(false)}>
                关闭
              </Button>
            ]}
            width={800}
          >
            {selectedResult && (
              <div className="space-y-4">
                <Descriptions title="基本信息" bordered size="small">
                  <Descriptions.Item label="算法" span={2}>
                    <Tag color={getAlgorithmColor(selectedResult.algorithm_name)}>
                      {selectedResult.algorithm_name}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="任务ID">
                    {selectedResult.task_id}
                  </Descriptions.Item>
                  <Descriptions.Item label="聚类数量">
                    {selectedResult.clusters_count}
                  </Descriptions.Item>
                  <Descriptions.Item label="轮廓系数">
                    <span className={selectedResult.silhouette_score > 0.3 ? 'text-green-600 font-semibold' : ''}>
                      {selectedResult.silhouette_score.toFixed(3)}
                    </span>
                  </Descriptions.Item>
                  <Descriptions.Item label="质量等级">
                    <Tag color={getQualityColor(selectedResult.silhouette_score)}>
                      {selectedResult.quality_level}
                    </Tag>
                  </Descriptions.Item>
                </Descriptions>

                <Descriptions title="检测结果" bordered size="small">
                  <Descriptions.Item label="总地址数">
                    {selectedResult.total_addresses.toLocaleString()}
                  </Descriptions.Item>
                  <Descriptions.Item label="机器人地址数">
                    {selectedResult.bot_addresses_count.toLocaleString()}
                  </Descriptions.Item>
                  <Descriptions.Item label="正常地址数">
                    {selectedResult.normal_addresses_count.toLocaleString()}
                  </Descriptions.Item>
                  <Descriptions.Item label="机器人检测率">
                    <Tag color={getDetectionRateColor(selectedResult.bot_addresses_pct)}>
                      {selectedResult.bot_addresses_pct.toFixed(2)}%
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="正常地址率">
                    {selectedResult.normal_addresses_pct.toFixed(2)}%
                  </Descriptions.Item>
                  <Descriptions.Item label="噪声点数">
                    {selectedResult.noise_points.toLocaleString()} ({selectedResult.noise_points_pct.toFixed(2)}%)
                  </Descriptions.Item>
                </Descriptions>

                <Descriptions title="技术指标" bordered size="small">
                  <Descriptions.Item label="特征维数">
                    {selectedResult.feature_count}
                  </Descriptions.Item>
                  <Descriptions.Item label="数据格式">
                    {selectedResult.data_format}
                  </Descriptions.Item>
                  <Descriptions.Item label="处理时间">
                    {selectedResult.processing_time.toFixed(3)}秒
                  </Descriptions.Item>
                  <Descriptions.Item label="检测水平" span={3}>
                    <Tag color={getDetectionRateColor(selectedResult.bot_addresses_pct)}>
                      {selectedResult.detection_rate_level}
                    </Tag>
                  </Descriptions.Item>
                </Descriptions>

                <Descriptions title="时间信息" bordered size="small">
                  <Descriptions.Item label="创建时间" span={3}>
                    {new Date(selectedResult.created_at).toLocaleString()}
                  </Descriptions.Item>
                </Descriptions>
              </div>
            )}
          </Modal>


        </div>
      </MainLayout>
    </ProtectedRoute>
  );
}