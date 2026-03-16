# 🎓 AI Learning Coach - AI学习教练系统

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.3+-brightgreen.svg)](https://vuejs.org/)
[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**智能化、个性化的 AI 驱动学习辅导系统**

[快速开始](#-快速开始) • [功能特性](#-功能特性) • [技术架构](#-技术架构) • [部署文档](DEPLOYMENT.md) • [贡献指南](#-贡献)

</div>

---

## 📖 项目简介

AI Learning Coach 是一个基于大语言模型（LLM）的智能学习辅导系统，通过 Multi-Agent 架构、RAG（检索增强生成）技术和个性化用户画像，为学习者提供：

- 🤖 **智能对话辅导** - 支持多种学习场景的 AI 助手
- 📊 **学习进度分析** - 数据驱动的学习效果评估
- 🎯 **个性化学习路径** - 基于用户画像的定制化规划
- ✅ **任务管理** - 高效的学习任务跟踪系统
- 📈 **可视化报告** - 直观的学习数据展示

## ✨ 功能特性

### 🎯 核心功能

| 功能模块 | 描述 | 技术亮点 |
|---------|------|---------|
| **智能对话** | Multi-Agent 智能路由，支持技术问答、进度分析、学习规划、项目指导 | GPT-4 + RAG + Agent编排 |
| **学习路径** | 个性化学习路径生成与可视化 | 用户画像 + 智能推荐 |
| **进度跟踪** | 多维度学习数据统计与分析 | ECharts 数据可视化 |
| **任务管理** | 看板式任务管理，支持优先级、状态追踪 | 拖拽排序 + 实时更新 |
| **用户画像** | 动态用户画像构建与更新 | 对话历史分析 |

### 🤖 Multi-Agent 架构

系统包含 4 个专业 Agent，自动识别用户意图并路由：

- **QA Agent (技术问答)** - 基于知识库的技术问题解答
- **Planner Agent (学习规划)** - 生成个性化学习计划
- **Analyst Agent (进度分析)** - 分析学习数据，生成报告
- **Coach Agent (项目指导)** - 提供项目开发建议和代码指导

### 🔥 技术亮点

- ✅ **真正的流式输出** - SSE 实时流式响应，打字机效果
- ✅ **向量检索增强** - Milvus 向量数据库 + 混合检索
- ✅ **异步任务处理** - Celery 分布式任务队列
- ✅ **完整的用户体系** - JWT 认证 + 权限控制
- ✅ **Docker 一键部署** - 全栈容器化，开箱即用

## 🚀 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ 内存
- OpenAI API Key (或兼容的 API 服务)

### 一键部署

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd AILearningCoach

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置以下必填项：
# - POSTGRES_PASSWORD: 数据库密码
# - SECRET_KEY: JWT密钥
# - OPENAI_API_KEY: OpenAI API密钥

# 3. 执行部署脚本
./deploy.sh
```

等待 3-5 分钟，系统将自动完成：
- 构建 Docker 镜像
- 启动所有服务（前端、后端、数据库等）
- 执行数据库初始化
- 健康检查

部署成功后访问：

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 其他命令

```bash
# 查看服务日志
./deploy.sh --logs

# 停止服务
./deploy.sh --stop

# 清理重新部署
./deploy.sh --clean

# 健康检查
./deploy.sh --health

# 查看帮助
./deploy.sh --help
```

详细部署说明请参考 [部署文档](DEPLOYMENT.md)

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          前端应用层                              │
│  Vue 3 + TypeScript + Element Plus + Vite + Pinia              │
│  ├─ 登录/注册  ├─ 智能对话  ├─ 学习路径  ├─ 任务管理            │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/SSE
┌─────────────────────────────────────────────────────────────────┐
│                      Nginx 反向代理层                            │
│  静态资源服务 + API 代理 + SSE 流式支持                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        后端应用层                                │
│  FastAPI + SQLAlchemy + Pydantic                               │
│  ├─ RESTful API  ├─ 认证授权  ├─ 业务逻辑                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       AI 服务层                                  │
│  Multi-Agent 编排器 + RAG 生成器 + LLM 客户端                   │
│  ├─ QA Agent  ├─ Planner  ├─ Analyst  ├─ Coach                │
└─────────────────────────────────────────────────────────────────┘
                    ↓                    ↓
┌──────────────────────────┐  ┌──────────────────────────┐
│    向量数据库层          │  │      关系数据库层        │
│  Milvus + MinIO + Etcd  │  │   PostgreSQL + Redis    │
│  ├─ 向量检索             │  │   ├─ 业务数据           │
│  ├─ 语义搜索             │  │   ├─ 用户信息           │
│  └─ 知识库存储           │  │   └─ 缓存管理           │
└──────────────────────────┘  └──────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                      异步任务层                                  │
│  Celery Worker + Celery Beat                                   │
│  ├─ 异步任务  ├─ 定时任务  ├─ 画像更新  ├─ 报告生成             │
└─────────────────────────────────────────────────────────────────┘
```

### 技术栈

#### 后端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| FastAPI | 0.104+ | Web 框架 |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | 15+ | 关系数据库 |
| Redis | 7+ | 缓存 |
| Milvus | 2.3+ | 向量数据库 |
| Celery | 5.3+ | 异步任务 |
| OpenAI | 1.3+ | LLM API |

#### 前端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.3+ | 前端框架 |
| TypeScript | 5.0+ | 类型系统 |
| Vite | 5.0+ | 构建工具 |
| Element Plus | 2.4+ | UI 组件库 |
| Pinia | 2.1+ | 状态管理 |
| Axios | 1.6+ | HTTP 客户端 |
| ECharts | 5.4+ | 数据可视化 |

#### DevOps

- Docker & Docker Compose
- Nginx
- Shell Scripts

## 📂 项目结构

```
AILearningCoach/
├── app/                      # 后端代码
│   ├── ai/                   # AI 模块
│   │   ├── agents/           # Multi-Agent 系统
│   │   │   ├── orchestrator.py    # Agent 编排器
│   │   │   ├── qa_agent.py        # 问答 Agent
│   │   │   ├── planner_agent.py   # 规划 Agent
│   │   │   ├── analyst_agent.py   # 分析 Agent
│   │   │   └── coach_agent.py     # 指导 Agent
│   │   └── rag/              # RAG 模块
│   │       ├── generator.py       # 答案生成器
│   │       ├── retriever.py       # 检索器
│   │       ├── llm.py             # LLM 客户端
│   │       └── embeddings.py      # 向量嵌入
│   ├── api/                  # API 路由
│   ├── models/               # 数据模型
│   ├── schemas/              # Pydantic 模式
│   ├── services/             # 业务服务
│   └── core/                 # 核心配置
├── frontend/                 # 前端代码
│   ├── src/
│   │   ├── api/              # API 服务
│   │   ├── components/       # 组件
│   │   ├── views/            # 页面视图
│   │   ├── stores/           # Pinia 状态
│   │   ├── router/           # 路由配置
│   │   └── utils/            # 工具函数
│   ├── Dockerfile            # 前端 Docker 配置
│   └── nginx.conf            # Nginx 配置
├── docker-compose.yml        # Docker 编排配置
├── deploy.sh                 # 一键部署脚本
├── .env.example              # 环境变量模板
├── DEPLOYMENT.md             # 部署文档
└── README.md                 # 本文件
```

## 📸 功能截图

### 智能对话

![智能对话](frontend/public/image/聊天页面.png)

支持流式输出、Multi-Agent 智能路由、对话历史管理

### 学习路径

![学习路径](frontend/public/image/学习路径.png)

个性化学习路径生成与可视化展示

### 任务管理

![任务管理](frontend/public/image/任务管理.png)

看板式任务管理，支持拖拽排序、状态更新

### 学习进度

![学习进度](frontend/public/image/学习进度.png)

多维度学习数据统计与可视化分析

## 🔧 开发指南

### 本地开发

#### 后端开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动数据库（使用 Docker）
docker-compose up -d db redis milvus-standalone

# 运行数据库迁移
python scripts/init_db.py

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 代码规范

- 后端：遵循 PEP 8 规范，使用 Black 格式化
- 前端：遵循 Vue 3 官方风格指南，使用 ESLint + Prettier

## 🧪 测试

```bash
# 后端单元测试
pytest tests/

# 前端单元测试
cd frontend
npm run test
```

## 📊 性能指标

- API 响应时间: < 200ms (P95)
- 向量检索延迟: < 100ms
- 流式首字响应: < 2s
- 并发支持: 100+ 用户

## 🗺️ Roadmap

- [x] Multi-Agent 智能对话系统
- [x] RAG 知识库检索
- [x] 学习路径生成
- [x] 任务管理系统
- [x] 用户画像系统
- [ ] 移动端适配
- [ ] 语音交互支持
- [ ] 学习社区功能
- [ ] 更多 LLM 模型支持
- [ ] 多语言支持

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式前端框架
- [Element Plus](https://element-plus.org/) - 优秀的 UI 组件库
- [Milvus](https://milvus.io/) - 高性能向量数据库
- [OpenAI](https://openai.com/) - 强大的 LLM API

## 📞 联系方式

- 项目主页: [GitHub Repository](https://github.com/yourusername/AILearningCoach)
- 问题反馈: [Issues](https://github.com/yourusername/AILearningCoach/issues)
- 邮箱: your.email@example.com

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐️ Star 支持一下！**

Made with ❤️ by [Your Name]

</div>
