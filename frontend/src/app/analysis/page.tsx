'use client';

import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Button, Form, Input, Select, 
  InputNumber, message, Modal, Steps, Space, Alert 
} from 'antd';
import { 
  ExperimentOutlined, 
  SettingOutlined, 
  PlayCircleOutlined,
  InfoCircleOutlined 
} from '@ant-design/icons';
import ProtectedRoute from '@/components/ProtectedRoute';
import MainLayout from '@/components/Layout/MainLayout';
import apiClient, { Dataset } from '@/lib/api';

interface AlgorithmInfo {
  name: string;
  description: string;
  advantages: string[];
  suitable_scenarios: string[];
  parameters: Record<string, any>;
}

interface CreateTaskForm {
  name: string;
  description?: string;
  algorithm_name: string;
  dataset_id: number;
  parameters?: Record<string, any>;
}

export default function AnalysisPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [algorithms, setAlgorithms] = useState<Record<string, AlgorithmInfo>>({});
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string>('');
  const [algorithmDetails, setAlgorithmDetails] = useState<AlgorithmInfo | null>(null);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const [datasetsResponse, algorithmsResponse] = await Promise.all([
        apiClient.getDatasets(),
        apiClient.getAlgorithms()
      ]);
      
      setDatasets(datasetsResponse.datasets || []);
      setAlgorithms(algorithmsResponse.algorithms || {});
    } catch (error) {
      message.error('获取数据失败');
    }
  };

  const fetchAlgorithmDetails = async (algorithmName: string) => {
    try {
      const response = await apiClient.getAlgorithmInfo(algorithmName);
      setAlgorithmDetails(response.algorithm);
    } catch (error) {
      message.error('获取算法详情失败');
    }
  };

  const handleAlgorithmSelect = (algorithmName: string) => {
    setSelectedAlgorithm(algorithmName);
    fetchAlgorithmDetails(algorithmName);
  };

  const handleCreateTask = () => {
    if (!selectedAlgorithm) {
      message.error('请先选择算法');
      return;
    }
    setCreateModalVisible(true);
  };

  const handleSubmitTask = async (values: CreateTaskForm) => {
    try {
      setLoading(true);
      const taskData = {
        ...values,
        algorithm_name: selectedAlgorithm,
      };
      
      await apiClient.createTask(taskData);
      message.success('任务创建成功');
      setCreateModalVisible(false);
      form.resetFields();
    } catch (error: any) {
      message.error(error?.response?.data?.message || '创建任务失败');
    } finally {
      setLoading(false);
    }
  };

  // 算法卡片配置
  const algorithmCards = [
    {
      key: 'DBSCAN',
      title: 'DBSCAN 聚类算法',
      description: '基于密度的聚类算法，能够发现任意形状的聚类并识别噪声点',
      features: [
        '无需预设聚类数量',
        '能处理任意形状的聚类',
        '自动识别噪声点',
        '对异常值鲁棒性强'
      ],
      icon: '🔍',
      color: '#1890ff'
    },
    {
      key: 'IsolationForest',
      title: 'Isolation Forest',
      description: '专门用于异常检测的算法，通过隔离异常点来识别机器人行为',
      features: [
        '专业异常检测算法',
        '不依赖正常数据分布',
        '计算效率高',
        '适合大规模数据'
      ],
      icon: '🌳',
      color: '#52c41a'
    },
    {
      key: 'KmeansPlus',
      title: 'K-means++ 聚类',
      description: '改进的K-means算法，通过优化初始中心点选择提高聚类效果',
      features: [
        '优化的初始化策略',
        '稳定的聚类结果',
        '适合球形聚类',
        '计算速度快'
      ],
      icon: '📊',
      color: '#faad14'
    }
  ];

  return (
    <ProtectedRoute>
      <MainLayout>
        <div className="bg-white min-h-screen -m-6 p-6">
          <div className="flex">
            {/* 左侧算法导航 */}
            <div className="w-64 pr-6 hidden lg:block">
              <div className="bg-white rounded-lg shadow-sm border p-4 sticky top-6">
                <div className="mb-6">
                  <div className="flex items-center mb-4">
                    <div className="w-6 h-6 bg-blue-500 rounded mr-3 flex items-center justify-center">
                      <span className="text-white text-sm">⚙</span>
                    </div>
                    <h3 className="font-semibold text-gray-800">可用算法</h3>
                  </div>
                  <div className="text-sm text-gray-600 mb-2">3</div>
                  <div className="text-xs text-gray-500">种可动态可用的检测算法</div>
                </div>

                <div className="mb-6">
                  <div className="flex items-center mb-4">
                    <div className="w-6 h-6 bg-orange-500 rounded mr-3 flex items-center justify-center">
                      <span className="text-white text-sm">⚡</span>
                    </div>
                    <h3 className="font-semibold text-gray-800">推荐算法</h3>
                  </div>
                  <div className="text-sm text-blue-600 cursor-pointer hover:text-blue-800">
                    DBSCAN
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    最准确检测
                  </div>
                </div>

                <div>
                  <div className="flex items-center mb-4">
                    <div className="w-6 h-6 bg-gray-500 rounded mr-3 flex items-center justify-center">
                      <span className="text-white text-sm">⚙</span>
                    </div>
                    <h3 className="font-semibold text-gray-800">参数优化</h3>
                  </div>
                  <div className="text-sm text-gray-600 mb-1">智能配置</div>
                  <div className="text-sm text-gray-600">自动参数优化</div>
                </div>
              </div>
            </div>

            {/* 主内容区域 */}
            <div className="flex-1">
              <div className="mb-6 flex justify-between items-center">
                <h1 className="text-2xl font-bold text-gray-800">分析任务</h1>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleCreateTask}
                  disabled={!selectedAlgorithm}
                  size="large"
                >
                  创建任务
                </Button>
              </div>

              {/* 步骤指引 */}
              <div className="mb-8">
                <div className="flex flex-col lg:flex-row lg:items-center lg:space-x-8 space-y-4 lg:space-y-0">
                  <div className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white mr-3 ${
                      selectedAlgorithm ? 'bg-blue-500' : 'bg-blue-500'
                    }`}>
                      <span className="text-sm">⚗</span>
                    </div>
                    <div>
                      <div className="font-medium text-gray-800">选择算法</div>
                      <div className="text-sm text-gray-500">根据数据特点选择合适的检测算法</div>
                    </div>
                  </div>
                  
                  <div className="flex-1 h-px bg-gray-300 hidden lg:block"></div>
                  
                  <div className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white mr-3 ${
                      selectedAlgorithm ? 'bg-blue-500' : 'bg-gray-300'
                    }`}>
                      <span className="text-sm">⚙</span>
                    </div>
                    <div>
                      <div className="font-medium text-gray-800">配置参数</div>
                      <div className="text-sm text-gray-500">查看算法详情并创建分析任务</div>
                    </div>
                  </div>
                  
                  <div className="flex-1 h-px bg-gray-300 hidden lg:block"></div>
                  
                  <div className="flex items-center">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-white mr-3 bg-gray-300">
                      <span className="text-sm">▶</span>
                    </div>
                    <div>
                      <div className="font-medium text-gray-800">执行分析</div>
                      <div className="text-sm text-gray-500">运行算法并查看检测结果</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 算法选择区域 */}
              <div>
                <h2 className="text-lg font-semibold mb-6">选择检测算法</h2>
                <Row gutter={[24, 24]}>
                  {algorithmCards.map((algorithm) => (
                    <Col xs={24} lg={8} key={algorithm.key}>
                      <Card
                        hoverable
                        className={`cursor-pointer transition-all duration-200 algorithm-card ${
                          selectedAlgorithm === algorithm.key 
                            ? 'algorithm-card-selected' 
                            : ''
                        }`}
                        onClick={() => handleAlgorithmSelect(algorithm.key)}
                      >
                        <div className="p-4">
                          <div className="flex items-center mb-4">
                            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                              <span className="text-2xl">{algorithm.icon}</span>
                            </div>
                            <div className="flex-1">
                              <h3 className="text-lg font-semibold text-gray-800 mb-1">
                                {algorithm.title}
                              </h3>
                              <div className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded inline-block">
                                v2.0.0
                              </div>
                            </div>
                          </div>
                          
                          <div className="mb-4">
                            <div className="text-sm text-gray-600 mb-2">算法类型：</div>
                            <div className="text-sm font-medium text-gray-800">{algorithm.description}</div>
                          </div>
                          
                          <div className="mb-4">
                            <div className="text-sm text-gray-600 mb-2">特点：</div>
                            <div className="space-y-1">
                              {algorithm.features.map((feature, index) => (
                                <div key={index} className="text-sm text-gray-700 flex items-center">
                                  <span className="text-green-500 mr-2">✓</span>
                                  {feature}
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          <div className="mb-4">
                            <div className="text-sm text-gray-600">性能：</div>
                            <div className="flex justify-between items-center mt-1">
                              <span className="text-xs text-gray-500">准确率{algorithm.key === 'DBSCAN' ? '94.6%' : algorithm.key === 'IsolationForest' ? '91.8%' : '89.3%'}</span>
                              <span className="text-xs text-gray-500">处理速度{algorithm.key === 'DBSCAN' ? '中等' : algorithm.key === 'IsolationForest' ? '较快' : '快'}</span>
                              <span className="text-xs text-gray-500">资源消耗{algorithm.key === 'DBSCAN' ? '中等' : algorithm.key === 'IsolationForest' ? '低' : '中等'}</span>
                            </div>
                          </div>
                          
                          <div className="flex justify-between items-center pt-4 border-t">
                            <Button 
                              type="primary" 
                              className={selectedAlgorithm === algorithm.key ? 'bg-blue-600' : ''}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAlgorithmSelect(algorithm.key);
                              }}
                            >
                              使用此算法
                            </Button>
                            <div className="flex space-x-2">
                              <Button type="text" size="small" icon={<SettingOutlined />}>
                                参数配置
                              </Button>
                              <Button type="text" size="small" icon={<InfoCircleOutlined />}>
                                详细信息
                              </Button>
                            </div>
                          </div>
                        </div>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </div>
            </div>
          </div>

          {/* 算法详情 */}
          {algorithmDetails && (
            <Card title="算法详细信息">
              <Row gutter={[24, 16]}>
                <Col xs={24} lg={12}>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-semibold text-gray-800 mb-2">算法描述</h4>
                      <p className="text-gray-600">{algorithmDetails.description}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-gray-800 mb-2">主要优势</h4>
                      <ul className="space-y-1">
                        {algorithmDetails.advantages?.map((advantage, index) => (
                          <li key={index} className="text-gray-600">
                            • {advantage}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Col>
                
                <Col xs={24} lg={12}>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-semibold text-gray-800 mb-2">适用场景</h4>
                      <ul className="space-y-1">
                        {algorithmDetails.suitable_scenarios?.map((scenario, index) => (
                          <li key={index} className="text-gray-600">
                            • {scenario}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    {algorithmDetails.parameters && (
                      <div>
                        <h4 className="font-semibold text-gray-800 mb-2">主要参数</h4>
                        <div className="space-y-2">
                          {Object.entries(algorithmDetails.parameters).map(([key, value]) => (
                            <div key={key} className="flex justify-between items-center text-sm">
                              <span className="text-gray-600">{key}:</span>
                              <span className="font-mono text-gray-800">{String(value)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Col>
              </Row>
            </Card>
          )}

          {/* 创建任务模态框 */}
          <Modal
            title="创建分析任务"
            open={createModalVisible}
            onCancel={() => {
              setCreateModalVisible(false);
              form.resetFields();
            }}
            footer={null}
            width={600}
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmitTask}
            >
              <Alert
                message={`已选择算法: ${selectedAlgorithm}`}
                type="info"
                showIcon
                className="mb-4"
              />

              <Form.Item
                name="name"
                label="任务名称"
                rules={[{ required: true, message: '请输入任务名称' }]}
              >
                <Input placeholder="请输入任务名称" />
              </Form.Item>

              <Form.Item
                name="description"
                label="任务描述"
              >
                <Input.TextArea
                  rows={3}
                  placeholder="请输入任务描述（可选）"
                />
              </Form.Item>

              <Form.Item
                name="dataset_id"
                label="选择数据集"
                rules={[{ required: true, message: '请选择数据集' }]}
              >
                <Select placeholder="请选择数据集">
                  {datasets
                    .filter(dataset => dataset.is_valid)
                    .map(dataset => (
                    <Select.Option key={dataset.id} value={dataset.id}>
                      <div>
                        <div>{dataset.name}</div>
                        <div className="text-xs text-gray-500">
                          {dataset.record_count?.toLocaleString()} 条记录 | {dataset.data_format}
                        </div>
                      </div>
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>

              {/* 算法参数配置 */}
              {selectedAlgorithm === 'DBSCAN' && (
                <div className="space-y-4 p-4 bg-gray-50 rounded">
                  <h4 className="font-semibold">DBSCAN 参数配置</h4>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name={['parameters', 'eps']}
                        label="邻域半径 (eps)"
                        initialValue={0.5}
                      >
                        <InputNumber
                          min={0.1}
                          max={2.0}
                          step={0.1}
                          placeholder="默认: 0.5"
                          className="w-full"
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name={['parameters', 'min_samples']}
                        label="最小样本数"
                        initialValue={5}
                      >
                        <InputNumber
                          min={2}
                          max={20}
                          placeholder="默认: 5"
                          className="w-full"
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                </div>
              )}

              {selectedAlgorithm === 'IsolationForest' && (
                <div className="space-y-4 p-4 bg-gray-50 rounded">
                  <h4 className="font-semibold">Isolation Forest 参数配置</h4>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name={['parameters', 'contamination']}
                        label="异常比例"
                        initialValue={0.1}
                      >
                        <InputNumber
                          min={0.01}
                          max={0.5}
                          step={0.01}
                          placeholder="默认: 0.1"
                          className="w-full"
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name={['parameters', 'n_estimators']}
                        label="树的数量"
                        initialValue={100}
                      >
                        <InputNumber
                          min={50}
                          max={300}
                          step={10}
                          placeholder="默认: 100"
                          className="w-full"
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                </div>
              )}

              {selectedAlgorithm === 'KmeansPlus' && (
                <div className="space-y-4 p-4 bg-gray-50 rounded">
                  <h4 className="font-semibold">K-means++ 参数配置</h4>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item
                        name={['parameters', 'n_clusters']}
                        label="聚类数量"
                        initialValue={3}
                      >
                        <InputNumber
                          min={2}
                          max={10}
                          placeholder="默认: 3"
                          className="w-full"
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        name={['parameters', 'max_iter']}
                        label="最大迭代次数"
                        initialValue={300}
                      >
                        <InputNumber
                          min={100}
                          max={1000}
                          step={50}
                          placeholder="默认: 300"
                          className="w-full"
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                </div>
              )}

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={loading}
                    icon={<PlayCircleOutlined />}
                  >
                    创建并启动任务
                  </Button>
                  <Button onClick={() => {
                    setCreateModalVisible(false);
                    form.resetFields();
                  }}>
                    取消
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Modal>
        </div>
      </MainLayout>
    </ProtectedRoute>
  );
}