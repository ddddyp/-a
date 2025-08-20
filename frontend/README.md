# 区块链交易机器人检测系统 - 前端

基于 Next.js 14 + Ant Design 5 构建的现代化前端应用，用于区块链交易机器人检测系统的用户界面。

## 技术栈

- **框架**: Next.js 14 (App Router)
- **UI库**: Ant Design 5.x
- **状态管理**: React Context API
- **HTTP客户端**: Axios
- **图表库**: ECharts (echarts-for-react)
- **样式方案**: Tailwind CSS
- **类型检查**: TypeScript

## 功能特性

### 🔐 认证系统
- JWT令牌认证
- 自动登录状态检查
- 路由权限保护

### 📊 仪表板
- 数据统计概览
- 实时图表展示
- 系统状态监控

### 📁 数据集管理
- 文件上传 (CSV/JSON/Excel)
- 数据预览和验证
- 文件格式自动识别

### 🔬 分析任务
- 三种算法选择 (DBSCAN/IsolationForest/KmeansPlus)
- 参数配置界面
- 任务创建向导

### 📋 任务监控
- 实时任务状态更新
- 进度条显示
- 任务控制操作

### 📈 结果展示
- 多维度数据可视化
- 结果对比分析
- 数据导出功能

## 项目结构

```
src/
├── app/                    # Next.js App Router
│   ├── globals.css        # 全局样式
│   ├── layout.tsx         # 根布局
│   ├── page.tsx          # 首页 (仪表板)
│   ├── login/            # 登录页面
│   ├── datasets/         # 数据集管理
│   ├── analysis/         # 分析任务
│   ├── tasks/           # 任务监控
│   └── results/         # 结果展示
├── components/           # 公共组件
│   ├── Layout/          # 布局组件
│   └── ProtectedRoute.tsx
├── contexts/            # React Context
│   └── AuthContext.tsx
└── lib/                # 工具库
    └── api.ts          # API客户端
```

## 环境配置

### 开发环境
1. 安装依赖
```bash
npm install
```

2. 配置环境变量
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1
```

3. 启动开发服务器
```bash
npm run dev
```

4. 访问应用
```
http://localhost:3000
```

### 生产环境
```bash
# 构建应用
npm run build

# 启动生产服务器
npm start
```

## API 集成

前端通过统一的 API 客户端与后端 Flask 服务通信：

- **认证**: JWT令牌自动管理
- **错误处理**: 统一错误拦截和提示
- **请求超时**: 30秒超时保护
- **文件上传**: 支持大文件上传

## 页面说明

### 仪表板 (`/`)
- 系统统计概览
- 算法使用分布图
- 任务状态分布图
- 最近任务列表

### 数据集管理 (`/datasets`)
- 文件上传界面
- 数据集列表展示
- 数据预览功能
- 文件格式验证

### 分析任务 (`/analysis`)
- 算法选择卡片
- 参数配置表单
- 任务创建流程

### 任务监控 (`/tasks`)
- 任务列表展示
- 实时状态更新
- 任务操作控制
- 详情查看模态框

### 结果展示 (`/results`)
- 结果数据表格
- 性能图表展示
- 结果对比功能
- 数据导出下载

## 样式设计

### 颜色主题
- 主色调: #1890ff (Ant Design 蓝)
- 成功色: #52c41a
- 警告色: #faad14
- 错误色: #ff4d4f

### 响应式设计
- 支持桌面端和移动端
- Ant Design 栅格系统
- 弹性布局适配

## 数据流管理

### 认证状态
- Context Provider 全局状态管理
- localStorage 令牌持久化
- 自动登录状态检查

### API 数据
- Axios 请求拦截器
- 统一错误处理机制
- 自动令牌刷新

## 开发规范

### 代码风格
- TypeScript 严格模式
- ESLint 代码检查
- 组件命名规范

### 组件设计
- 函数式组件 + Hooks
- Props 类型定义
- 错误边界处理

## 部署说明

### Docker 部署
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### 环境变量
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

## 性能优化

- **代码分割**: 动态导入大型组件
- **图片优化**: Next.js Image 组件
- **缓存策略**: API 响应缓存
- **懒加载**: 图表组件按需加载

## 浏览器支持

- Chrome >= 88
- Firefox >= 85
- Safari >= 14
- Edge >= 88

## 开发团队

- 前端架构设计
- UI/UX 界面设计
- 数据可视化开发
- 性能优化实施