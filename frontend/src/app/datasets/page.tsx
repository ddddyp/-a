'use client';

import React, { useState, useEffect } from 'react';
import { 
  Table, Card, Button, Upload, Modal, Form, Input, message, 
  Space, Popconfirm, Tag, Progress, Tooltip, Row, Col, Statistic 
} from 'antd';
import { 
  UploadOutlined, 
  DeleteOutlined, 
  EyeOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import ProtectedRoute from '@/components/ProtectedRoute';
import MainLayout from '@/components/Layout/MainLayout';
import apiClient, { Dataset } from '@/lib/api';
import type { ColumnsType } from 'antd/es/table';
import type { UploadFile } from 'antd/es/upload/interface';

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [statistics, setStatistics] = useState<any>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchDatasets();
    fetchStatistics();
  }, []);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getDatasets();
      setDatasets(response.datasets || []);
    } catch (error: any) {
      message.error('获取数据集列表失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await apiClient.getDatasetStatistics();
      setStatistics(response);
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  const handleUpload = async (values: any) => {
    const { file, name, description } = values;
    
    if (!file || file.length === 0) {
      message.error('请选择文件');
      return;
    }

    const formData = new FormData();
    formData.append('file', file[0].originFileObj);
    formData.append('name', name);
    if (description) {
      formData.append('description', description);
    }

    try {
      await apiClient.uploadDataset(formData);
      message.success('数据集上传成功');
      setUploadModalVisible(false);
      form.resetFields();
      fetchDatasets();
      fetchStatistics();
    } catch (error: any) {
      message.error(error?.response?.data?.message || '上传失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiClient.deleteDataset(id);
      message.success('删除成功');
      fetchDatasets();
      fetchStatistics();
    } catch (error: any) {
      message.error('删除失败');
    }
  };

  const handlePreview = async (dataset: Dataset) => {
    try {
      const response = await apiClient.previewDataset(dataset.id, 10);
      setPreviewData({
        dataset,
        preview: response.preview || {},
        dataset_info: response.dataset_info || {}
      });
      setPreviewModalVisible(true);
    } catch (error: any) {
      message.error('预览失败');
    }
  };

  const getFileTypeColor = (fileType: string): string => {
    const colors: Record<string, string> = {
      'csv': 'green',
      'json': 'blue',
      'xlsx': 'orange'
    };
    return colors[fileType] || 'default';
  };

  const getDataFormatColor = (format?: string): string => {
    const colors: Record<string, string> = {
      'BLTE': 'purple',
      'Transaction': 'cyan',
      'Generic': 'geekblue'
    };
    return colors[format || ''] || 'default';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const columns: ColumnsType<Dataset> = [
    {
      title: '数据集名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      ellipsis: true,
    },
    {
      title: '原始文件名',
      dataIndex: 'original_filename',
      key: 'original_filename',
      width: 180,
      ellipsis: true,
    },
    {
      title: '文件类型',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 100,
      render: (type: string) => (
        <Tag color={getFileTypeColor(type)}>{type.toUpperCase()}</Tag>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '记录数',
      dataIndex: 'record_count',
      key: 'record_count',
      width: 100,
      render: (count: number) => count?.toLocaleString() || '-',
    },
    {
      title: '列数',
      dataIndex: 'column_count',
      key: 'column_count',
      width: 80,
      align: 'center',
    },
    {
      title: '数据格式',
      dataIndex: 'data_format',
      key: 'data_format',
      width: 120,
      render: (format?: string) => (
        format ? <Tag color={getDataFormatColor(format)}>{format}</Tag> : '-'
      ),
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          {record.is_valid ? (
            <Tag icon={<CheckCircleOutlined />} color="success">有效</Tag>
          ) : (
            <Tag color="error">无效</Tag>
          )}
          {record.processed && (
            <Tag color="processing">已处理</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      width: 150,
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Tooltip title="预览数据">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handlePreview(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定删除此数据集吗？"
            description="删除后无法恢复，相关任务也会被删除。"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除数据集">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <ProtectedRoute>
      <MainLayout>
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-800">数据集管理</h1>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setUploadModalVisible(true)}
            >
              上传数据集
            </Button>
          </div>

          {/* 统计卡片 */}
          {statistics && (
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8} lg={6}>
                <Card>
                  <Statistic
                    title="数据集总数"
                    value={statistics.total_datasets || 0}
                    prefix={<DatabaseOutlined />}
                    suffix="个"
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8} lg={6}>
                <Card>
                  <Statistic
                    title="有效数据集"
                    value={statistics.valid_datasets || 0}
                    prefix={<CheckCircleOutlined />}
                    suffix="个"
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8} lg={6}>
                <Card>
                  <Statistic
                    title="总文件大小"
                    value={formatFileSize(statistics.total_size || 0)}
                    prefix={<FileTextOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8} lg={6}>
                <Card>
                  <Statistic
                    title="总记录数"
                    value={(statistics.total_records || 0).toLocaleString()}
                    prefix={<DatabaseOutlined />}
                  />
                </Card>
              </Col>
            </Row>
          )}

          {/* 数据集表格 */}
          <Card>
            <Table
              columns={columns}
              dataSource={datasets}
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

          {/* 上传数据集模态框 */}
          <Modal
            title="上传数据集"
            open={uploadModalVisible}
            onCancel={() => {
              setUploadModalVisible(false);
              form.resetFields();
            }}
            footer={null}
            width={600}
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleUpload}
            >
              <Form.Item
                name="name"
                label="数据集名称"
                rules={[{ required: true, message: '请输入数据集名称' }]}
              >
                <Input placeholder="请输入数据集名称" />
              </Form.Item>

              <Form.Item
                name="description"
                label="描述"
              >
                <Input.TextArea
                  rows={3}
                  placeholder="请输入数据集描述（可选）"
                />
              </Form.Item>

              <Form.Item
                name="file"
                label="选择文件"
                rules={[{ required: true, message: '请选择文件' }]}
                valuePropName="fileList"
                getValueFromEvent={(e) => {
                  if (Array.isArray(e)) {
                    return e;
                  }
                  return e?.fileList;
                }}
              >
                <Upload
                  accept=".csv,.json,.xlsx"
                  maxCount={1}
                  beforeUpload={() => false} // 阻止自动上传
                >
                  <Button icon={<UploadOutlined />}>选择文件</Button>
                </Upload>
              </Form.Item>

              <div className="text-sm text-gray-500 mb-4">
                <p>支持的文件格式：CSV、JSON、Excel (.xlsx)</p>
                <p>最大文件大小：100MB</p>
              </div>

              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit">
                    上传
                  </Button>
                  <Button onClick={() => {
                    setUploadModalVisible(false);
                    form.resetFields();
                  }}>
                    取消
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Modal>

          {/* 数据预览模态框 */}
          <Modal
            title={`数据预览 - ${previewData?.dataset?.name}`}
            open={previewModalVisible}
            onCancel={() => setPreviewModalVisible(false)}
            footer={[
              <Button key="close" onClick={() => setPreviewModalVisible(false)}>
                关闭
              </Button>
            ]}
            width={1000}
          >
            {previewData && (
              <div>
                <div className="mb-4 p-4 bg-gray-50 rounded">
                  <Row gutter={16}>
                    <Col span={6}>
                      <div>
                        <div className="text-gray-600">记录数</div>
                        <div className="text-lg font-semibold">
                          {previewData.dataset.record_count?.toLocaleString() || '-'}
                        </div>
                      </div>
                    </Col>
                    <Col span={6}>
                      <div>
                        <div className="text-gray-600">列数</div>
                        <div className="text-lg font-semibold">
                          {previewData.dataset.column_count || '-'}
                        </div>
                      </div>
                    </Col>
                    <Col span={6}>
                      <div>
                        <div className="text-gray-600">文件大小</div>
                        <div className="text-lg font-semibold">
                          {formatFileSize(previewData.dataset.file_size)}
                        </div>
                      </div>
                    </Col>
                    <Col span={6}>
                      <div>
                        <div className="text-gray-600">数据格式</div>
                        <div className="text-lg font-semibold">
                          {previewData.dataset.data_format || '未知'}
                        </div>
                      </div>
                    </Col>
                  </Row>
                </div>
                
                {previewData.preview && previewData.preview.data && previewData.preview.data.length > 0 ? (
                  <div>
                    <h4 className="mb-3">前{previewData.preview.data.length}行数据预览</h4>
                    <div className="overflow-auto max-h-96">
                      <Table
                        dataSource={previewData.preview.data}
                        columns={previewData.preview.columns?.map((col: string, index: number) => ({
                          title: col,
                          dataIndex: col,
                          key: col,
                          width: 150,
                          ellipsis: true,
                          render: (value: any) => {
                            if (typeof value === 'number') {
                              return value.toLocaleString();
                            }
                            return String(value || '-');
                          }
                        })) || []}
                        pagination={false}
                        size="small"
                        scroll={{ x: 'max-content' }}
                        rowKey={(record, index) => index || 0}
                      />
                    </div>
                    <div className="mt-2 text-sm text-gray-500">
                      数据类型: {previewData.preview.shape ? `${previewData.preview.shape[0]} 行 × ${previewData.preview.shape[1]} 列` : ''}
                      {previewData.preview.total_records && (
                        <span> | 总记录数: {previewData.preview.total_records.toLocaleString()}</span>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    暂无预览数据
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