# AI学习教练系统 - 前端

基于 Vue 3 + TypeScript + Vite + Element Plus 的现代化Web应用

## 🚀 快速开始

### 安装依赖

```bash
npm install
# 或
pnpm install
```

### 开发环境运行

```bash
npm run dev
```

访问 http://localhost:3000

### 生产环境构建

```bash
npm run build
```

### 预览构建结果

```bash
npm run preview
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── api/              # API接口封装
│   ├── assets/           # 静态资源
│   ├── components/       # 公共组件
│   ├── layouts/          # 布局组件
│   ├── router/           # 路由配置
│   ├── stores/           # Pinia状态管理
│   ├── types/            # TypeScript类型定义
│   ├── utils/            # 工具函数
│   ├── views/            # 页面组件
│   ├── App.vue           # 根组件
│   └── main.ts           # 入口文件
├── public/               # 公共资源
├── index.html            # HTML模板
├── vite.config.ts        # Vite配置
├── tsconfig.json         # TypeScript配置
└── package.json          # 项目依赖
```

## 🎯 主要功能

- ✅ 用户认证（登录/注册）
- ✅ 主仪表盘（数据概览）
- ✅ Multi-Agent智能对话
- ✅ 学习路径可视化
- ✅ 任务管理看板
- ✅ 学习进度与报告
- ✅ 用户画像管理

## 🛠️ 技术栈

- **框架**: Vue 3.4+
- **语言**: TypeScript 5.0+
- **构建工具**: Vite 5.0+
- **UI组件库**: Element Plus 2.5+
- **路由**: Vue Router 4
- **状态管理**: Pinia 2.1+
- **HTTP客户端**: Axios
- **图表**: ECharts 5
- **样式**: SCSS

## 🔌 API配置

后端API地址配置在 `.env.development` 文件中：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 📝 开发规范

- 组件使用 `<script setup>` 语法
- TypeScript严格模式
- ESLint代码检查
- Prettier代码格式化

## 🎨 UI设计参考

UI设计图位于项目根目录的 `assets` 文件夹中。

## 📞 联系方式

如有问题，请联系开发团队。
