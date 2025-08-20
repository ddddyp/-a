import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

export interface User {
  id: number;
  username: string;
  email?: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
  dataset_count: number;
  task_count: number;
}

export interface Dataset {
  id: number;
  name: string;
  description?: string;
  original_filename: string;
  filename: string;
  file_type: string;
  file_size: number;
  record_count?: number;
  column_count?: number;
  data_format?: string;
  processed: boolean;
  processed_at?: string;
  is_valid: boolean;
  validation_info?: any;
  upload_time: string;
  user_id: number;
  task_count: number;
}

export interface Task {
  id: number;
  name: string;
  description?: string;
  algorithm_name: string;
  parameters?: any;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_stage?: string;
  error_message?: string;
  processing_time?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  user_id: number;
  dataset_id: number;
  result_count: number;
  dataset?: Dataset;
  latest_result?: Result;
}

export interface Result {
  id: number;
  algorithm_name: string;
  clusters_count: number;
  bot_addresses_count: number;
  bot_addresses_pct: number;
  normal_addresses_count: number;
  normal_addresses_pct: number;
  noise_points: number;
  noise_points_pct: number;
  silhouette_score: number;
  detection_accuracy: number;
  cluster_labels?: number[];
  cluster_stats?: any;
  evaluation_metrics?: any;
  total_addresses: number;
  feature_count: number;
  data_format: string;
  processing_time: number;
  created_at: string;
  task_id: number;
  quality_level: string;
  detection_rate_level: string;
}

class ApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 请求拦截器 - 添加认证token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器 - 统一错误处理
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token过期，跳转到登录页
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // 认证相关API
  async login(username: string, password: string) {
    const response = await this.client.post('/auth/login', {
      username,
      password,
    });
    return response.data;
  }

  async getProfile() {
    const response = await this.client.get('/auth/profile');
    return response.data;
  }

  // 算法相关API
  async getAlgorithms() {
    const response = await this.client.get('/algorithms');
    return response.data;
  }

  async getAlgorithmInfo(algorithmName: string) {
    const response = await this.client.get(`/algorithms/${algorithmName}/info`);
    return response.data;
  }

  async getAlgorithmParameters(algorithmName: string) {
    const response = await this.client.get(`/algorithms/${algorithmName}/parameters`);
    return response.data;
  }

  async getAlgorithmComparison() {
    const response = await this.client.get('/algorithms/comparison');
    return response.data;
  }

  // 数据集相关API
  async getDatasets() {
    const response = await this.client.get('/datasets');
    return response.data;
  }

  async uploadDataset(formData: FormData) {
    const response = await this.client.post('/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 文件上传超时时间更长
    });
    return response.data;
  }

  async getDataset(datasetId: number) {
    const response = await this.client.get(`/datasets/${datasetId}`);
    return response.data;
  }

  async previewDataset(datasetId: number, limit: number = 10) {
    const response = await this.client.get(`/datasets/${datasetId}/preview?limit=${limit}`);
    return response.data;
  }

  async deleteDataset(datasetId: number) {
    const response = await this.client.delete(`/datasets/${datasetId}`);
    return response.data;
  }

  async validateDataset(datasetId: number) {
    const response = await this.client.post(`/datasets/${datasetId}/validate`);
    return response.data;
  }

  async getDatasetStatistics() {
    const response = await this.client.get('/datasets/statistics');
    return response.data;
  }

  // 任务相关API
  async createTask(taskData: any) {
    const response = await this.client.post('/tasks', taskData);
    return response.data;
  }

  async getTasks() {
    const response = await this.client.get('/tasks');
    return response.data;
  }

  async getTask(taskId: number) {
    const response = await this.client.get(`/tasks/${taskId}`);
    return response.data;
  }

  async startTask(taskId: number) {
    const response = await this.client.post(`/tasks/${taskId}/start`);
    return response.data;
  }

  async cancelTask(taskId: number) {
    const response = await this.client.post(`/tasks/${taskId}/cancel`);
    return response.data;
  }

  async deleteTask(taskId: number) {
    const response = await this.client.delete(`/tasks/${taskId}`);
    return response.data;
  }

  async getRunningTasks() {
    const response = await this.client.get('/tasks/running');
    return response.data;
  }

  async getTaskStatistics() {
    const response = await this.client.get('/tasks/statistics');
    return response.data;
  }

  async getTaskServiceStatus() {
    const response = await this.client.get('/tasks/service/status');
    return response.data;
  }

  // 结果相关API
  async getResults() {
    const response = await this.client.get('/results');
    return response.data;
  }

  async getResult(resultId: number) {
    const response = await this.client.get(`/results/${resultId}`);
    return response.data;
  }

  async compareResults(resultIds: number[]) {
    const response = await this.client.post('/results/comparison', { result_ids: resultIds });
    return response.data;
  }

  async exportResult(resultId: number, format: string = 'csv') {
    const response = await this.client.get(`/results/${resultId}/export?format=${format}`, {
      responseType: 'blob'
    });
    return response.data;
  }

  async deleteResult(resultId: number) {
    const response = await this.client.delete(`/results/${resultId}`);
    return response.data;
  }

  async getResultStatistics() {
    const response = await this.client.get('/results/statistics');
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;