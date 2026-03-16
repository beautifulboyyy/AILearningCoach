# AI Learning Coach - 部署文档

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细部署步骤](#详细部署步骤)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [服务管理](#服务管理)

## 🖥️ 系统要求

### 硬件要求

- **CPU**: 4核以上
- **内存**: 8GB 以上（推荐 16GB）
- **存储**: 20GB 以上可用空间
- **网络**: 稳定的互联网连接（用于拉取镜像和 AI 模型调用）

### 软件要求

- **操作系统**: 
  - Linux (Ubuntu 20.04+, CentOS 7+)
  - macOS 10.15+
  - Windows 10/11 (with WSL2)
  
- **必需软件**:
  - Docker 20.10+
  - Docker Compose 2.0+ (或 docker-compose 1.29+)

## 🚀 快速开始

### 1. 克隆项目（如果还没有）

```bash
git clone <repository-url>
cd AILearningCoach
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，至少需要配置以下项：
# - POSTGRES_PASSWORD: 数据库密码
# - SECRET_KEY: JWT密钥
# - OPENAI_API_KEY: OpenAI API密钥
nano .env  # 或使用其他编辑器
```

### 3. 一键部署

```bash
# 给脚本添加执行权限（首次需要）
chmod +x deploy.sh

# 执行部署
./deploy.sh
```

等待几分钟，所有服务将自动构建并启动。部署成功后会显示访问地址。

## 📝 详细部署步骤

### 步骤 1: 环境准备

#### 安装 Docker

**Ubuntu/Debian:**

```bash
# 更新包索引
sudo apt-get update

# 安装依赖
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或运行
newgrp docker
```

**macOS:**

下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)

**Windows:**

下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

#### 验证安装

```bash
docker --version
docker compose version
```

### 步骤 2: 配置应用

#### 2.1 编辑环境变量

```bash
cp .env.example .env
```

**重要配置项说明：**

| 配置项 | 说明 | 必填 |
|--------|------|------|
| `POSTGRES_PASSWORD` | 数据库密码 | ✅ |
| `SECRET_KEY` | JWT密钥（随机字符串） | ✅ |
| `OPENAI_API_KEY` | OpenAI API密钥 | ✅ |
| `OPENAI_API_BASE` | API基础URL | ❌ |
| `OPENAI_MODEL` | 使用的模型名称 | ❌ |

**生成安全的 SECRET_KEY:**

```bash
# Python 方式
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL 方式
openssl rand -base64 32
```

#### 2.2 配置 AI 模型

**使用 OpenAI:**

```bash
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

**使用 DeepSeek (示例):**

```bash
OPENAI_API_KEY=sk-your-deepseek-api-key
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### 步骤 3: 部署服务

#### 3.1 首次部署

```bash
./deploy.sh
```

这将执行：
1. 检查系统环境
2. 构建 Docker 镜像
3. 启动所有服务
4. 等待服务就绪
5. 执行健康检查
6. 显示访问信息

#### 3.2 清理重新部署

如果需要清理所有数据重新开始：

```bash
./deploy.sh --clean
```

⚠️ **警告**: 此操作会删除所有数据，包括数据库！

### 步骤 4: 验证部署

部署完成后，访问以下地址验证：

- **前端应用**: http://localhost:3000
- **后端 API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

## ⚙️ 配置说明

### 服务架构

系统由以下服务组成：

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| 前端 | ai_coach_frontend | 3000 | Vue3 + Element Plus |
| 后端 | ai_coach_app | 8000 | FastAPI 应用 |
| 数据库 | ai_coach_db | 5432 | PostgreSQL |
| 缓存 | ai_coach_redis | 6379 | Redis |
| 向量数据库 | ai_coach_milvus | 19530 | Milvus |
| 对象存储 | ai_coach_minio | 9000, 9001 | MinIO |
| Celery Worker | ai_coach_celery_worker | - | 异步任务 |
| Celery Beat | ai_coach_celery_beat | - | 定时任务 |

### 数据持久化

数据存储在 Docker volumes 中：

- `postgres_data`: PostgreSQL 数据
- `redis_data`: Redis 数据
- `milvus_data`: Milvus 向量数据
- `minio_data`: MinIO 对象存储
- `etcd_data`: Etcd 配置数据

### 网络配置

所有服务在 `ai_coach_network` 网络中通信。

前端通过 Nginx 反向代理访问后端 API（`/api/` 路径）。

## 🔧 服务管理

### 常用命令

```bash
# 查看服务状态
./deploy.sh --health

# 查看日志
./deploy.sh --logs

# 查看特定服务日志
docker compose logs -f app          # 后端
docker compose logs -f frontend     # 前端
docker compose logs -f db          # 数据库

# 停止服务
./deploy.sh --stop

# 重启服务
docker compose restart

# 重启特定服务
docker compose restart app
docker compose restart frontend
```

### 进入容器

```bash
# 进入后端容器
docker exec -it ai_coach_app bash

# 进入前端容器
docker exec -it ai_coach_frontend sh

# 进入数据库
docker exec -it ai_coach_db psql -U postgres -d ai_learning_coach
```

### 数据备份

#### 备份数据库

```bash
# 导出数据库
docker exec ai_coach_db pg_dump -U postgres ai_learning_coach > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker exec -i ai_coach_db psql -U postgres ai_learning_coach < backup_20260128_120000.sql
```

#### 备份 Docker Volumes

```bash
# 创建备份目录
mkdir -p ./backups

# 备份所有 volumes
docker run --rm \
  -v ailearningcoach_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_data_$(date +%Y%m%d).tar.gz -C /data .
```

## ❓ 常见问题

### 1. 端口冲突

**问题**: 提示端口已被占用

**解决**:

```bash
# 查看端口占用
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :5432

# 停止占用端口的进程
sudo kill -9 <PID>

# 或修改 docker-compose.yml 中的端口映射
# 例如将 3000:80 改为 3001:80
```

### 2. Docker 镜像构建失败

**问题**: 构建前端镜像时 npm install 失败

**解决**:

```bash
# 清理 Docker 缓存
docker system prune -a

# 重新构建
./deploy.sh --clean
```

### 3. 数据库连接失败

**问题**: 后端无法连接数据库

**解决**:

```bash
# 检查数据库容器状态
docker ps | grep ai_coach_db

# 查看数据库日志
docker logs ai_coach_db

# 确认环境变量配置正确
cat .env | grep POSTGRES
```

### 4. API Key 相关错误

**问题**: AI 功能无法使用

**解决**:

1. 确认 `.env` 中 `OPENAI_API_KEY` 已正确配置
2. 验证 API Key 是否有效
3. 检查 API 调用额度
4. 查看后端日志排查具体错误

```bash
docker logs ai_coach_app | grep -i "api"
```

### 5. 前端无法访问后端

**问题**: 前端请求 API 失败

**解决**:

1. 确认后端服务已启动: `docker ps | grep ai_coach_app`
2. 检查网络连接: `docker network inspect ai_coach_network`
3. 查看 Nginx 配置: `docker exec ai_coach_frontend cat /etc/nginx/conf.d/default.conf`

### 6. Milvus 启动失败

**问题**: 向量数据库启动超时

**解决**:

```bash
# Milvus 需要较多资源，增加 Docker 内存限制
# Docker Desktop -> Settings -> Resources -> Memory: 至少 8GB

# 或单独重启 Milvus
docker compose restart milvus-standalone
```

## 🔐 安全建议

### 生产环境部署

1. **修改默认密码**
   - 数据库密码
   - Redis 密码（如果启用）
   - MinIO 访问密钥

2. **使用 HTTPS**
   - 配置 SSL 证书
   - 使用 Nginx/Caddy 作为反向代理

3. **限制端口暴露**
   - 只暴露必要的端口（80, 443）
   - 数据库端口不对外开放

4. **定期备份**
   - 设置自动备份任务
   - 测试恢复流程

5. **监控和日志**
   - 设置日志轮转
   - 配置监控告警

## 📞 获取帮助

- **查看帮助**: `./deploy.sh --help`
- **查看日志**: `./deploy.sh --logs`
- **健康检查**: `./deploy.sh --health`

## 📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

---

**祝您部署顺利！🎉**
