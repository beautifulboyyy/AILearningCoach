# ✅ 部署清单

## 📦 部署文件清单

| 文件 | 路径 | 说明 | 状态 |
|------|------|------|------|
| 部署脚本 | `./deploy.sh` | 一键部署脚本 | ✅ |
| 环境变量模板 | `./.env.example` | 环境变量配置模板 | ✅ |
| Docker编排 | `./docker-compose.yml` | 包含前后端所有服务 | ✅ |
| 前端Dockerfile | `./frontend/Dockerfile` | 前端构建配置 | ✅ |
| Nginx配置 | `./frontend/nginx.conf` | 前端服务器配置 | ✅ |
| 后端Dockerfile | `./Dockerfile` | 后端构建配置 | ✅ |
| 部署文档 | `./DEPLOYMENT.md` | 详细部署说明 | ✅ |
| 快速开始 | `./QUICKSTART.md` | 5分钟快速部署 | ✅ |
| README | `./README.md` | 项目说明文档 | ✅ |

## 🏗️ 服务架构

### Docker Compose 服务清单

| 服务名 | 容器名 | 端口 | 镜像 | 状态 |
|--------|--------|------|------|------|
| frontend | ai_coach_frontend | 3000:80 | 自构建 | ✅ |
| app | ai_coach_app | 8000:8000 | 自构建 | ✅ |
| db | ai_coach_db | 5432:5432 | postgres:15-alpine | ✅ |
| redis | ai_coach_redis | 6379:6379 | redis:7-alpine | ✅ |
| milvus-standalone | ai_coach_milvus | 19530, 9091 | milvusdb/milvus:v2.3.3 | ✅ |
| minio | ai_coach_minio | 9000, 9001 | minio/minio | ✅ |
| etcd | ai_coach_etcd | - | quay.io/coreos/etcd:v3.5.5 | ✅ |
| celery_worker | ai_coach_celery_worker | - | 自构建 | ✅ |
| celery_beat | ai_coach_celery_beat | - | 自构建 | ✅ |
| init | ai_coach_init | - | 自构建 (一次性) | ✅ |

### 数据卷

| 卷名 | 用途 |
|------|------|
| postgres_data | PostgreSQL 数据持久化 |
| redis_data | Redis 数据持久化 |
| milvus_data | Milvus 向量数据 |
| etcd_data | Etcd 配置数据 |
| minio_data | MinIO 对象存储 |
| init_marker | 初始化标记 |

## 🔧 部署前检查

### 1. 系统环境

- [ ] Docker 已安装 (20.10+)
- [ ] Docker Compose 已安装 (2.0+)
- [ ] 系统内存 ≥ 8GB
- [ ] 可用磁盘空间 ≥ 20GB
- [ ] 网络连接正常

### 2. 环境变量配置

- [ ] 复制 `.env.example` 为 `.env`
- [ ] 配置 `POSTGRES_PASSWORD`
- [ ] 配置 `SECRET_KEY`
- [ ] 配置 `OPENAI_API_KEY`
- [ ] (可选) 配置 `OPENAI_API_BASE`
- [ ] (可选) 配置邮件服务器

### 3. 端口检查

确保以下端口未被占用：

```bash
# 检查端口占用
lsof -i :3000  # 前端
lsof -i :8000  # 后端 API
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :19530 # Milvus
lsof -i :9000  # MinIO API
lsof -i :9001  # MinIO Console
```

## 📋 部署步骤

### 标准部署流程

```bash
# 1. 准备环境变量
cp .env.example .env
nano .env  # 编辑配置

# 2. 给脚本添加执行权限
chmod +x deploy.sh

# 3. 执行部署
./deploy.sh

# 4. 等待服务启动（3-5分钟）
# 查看实时日志（可选）
./deploy.sh --logs

# 5. 验证部署
./deploy.sh --health
```

### 清理重新部署

```bash
# ⚠️ 警告：会删除所有数据
./deploy.sh --clean
```

## ✅ 部署后验证

### 1. 服务健康检查

```bash
# 执行健康检查
./deploy.sh --health

# 预期输出：
# ✅ ai_coach_db: 运行中
# ✅ ai_coach_redis: 运行中
# ✅ ai_coach_milvus: 运行中
# ✅ ai_coach_app: 运行中
# ✅ ai_coach_frontend: 运行中
```

### 2. 访问测试

| 服务 | URL | 预期结果 |
|------|-----|----------|
| 前端首页 | http://localhost:3000 | 显示登录页面 |
| 后端健康检查 | http://localhost:8000/api/v1/health | `{"status": "ok"}` |
| API文档 | http://localhost:8000/docs | Swagger UI |
| Nginx健康 | http://localhost:3000/health | `healthy` |

### 3. 功能测试

- [ ] 用户注册成功
- [ ] 用户登录成功
- [ ] 访问主页数据正常
- [ ] 智能对话流式输出正常
- [ ] 学习路径生成成功
- [ ] 任务创建成功
- [ ] 学习进度显示正常

## 🔍 故障排查

### 问题：服务启动失败

```bash
# 1. 查看容器状态
docker compose ps

# 2. 查看错误日志
docker compose logs <service_name>

# 3. 检查环境变量
cat .env | grep -v "^#" | grep -v "^$"

# 4. 重新构建
docker compose build --no-cache
docker compose up -d
```

### 问题：前端无法访问后端

```bash
# 1. 检查网络
docker network inspect ai_coach_network

# 2. 测试后端连通性
docker exec ai_coach_frontend wget -O- http://app:8000/api/v1/health

# 3. 检查 Nginx 配置
docker exec ai_coach_frontend cat /etc/nginx/conf.d/default.conf
```

### 问题：数据库连接失败

```bash
# 1. 检查数据库状态
docker logs ai_coach_db

# 2. 测试数据库连接
docker exec ai_coach_app python scripts/test_db.py

# 3. 重置数据库
docker compose down -v
docker compose up -d db
# 等待数据库就绪
docker compose up -d
```

### 问题：Milvus 启动超时

```bash
# 1. 增加 Docker 内存限制
# Docker Desktop -> Settings -> Resources -> Memory: 至少 8GB

# 2. 单独启动 Milvus 依赖
docker compose up -d etcd minio
sleep 10
docker compose up -d milvus-standalone

# 3. 检查 Milvus 日志
docker logs ai_coach_milvus
```

## 📊 监控和维护

### 日志查看

```bash
# 查看所有服务日志
./deploy.sh --logs

# 查看特定服务
docker compose logs -f app
docker compose logs -f frontend
docker compose logs -f celery_worker

# 查看最近100行
docker compose logs --tail=100 app
```

### 资源监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df
```

### 数据备份

```bash
# 备份数据库
docker exec ai_coach_db pg_dump -U postgres ai_learning_coach > backup.sql

# 备份卷
docker run --rm \
  -v ailearningcoach_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_$(date +%Y%m%d).tar.gz -C /data .
```

## 🎯 生产环境额外配置

### 安全加固

- [ ] 修改所有默认密码
- [ ] 启用 HTTPS (配置 SSL 证书)
- [ ] 配置防火墙规则
- [ ] 启用 API 限流
- [ ] 配置日志轮转
- [ ] 设置监控告警

### 性能优化

- [ ] 调整 Postgres 连接池
- [ ] 配置 Redis 内存限制
- [ ] 优化 Nginx 缓存策略
- [ ] 启用 CDN (静态资源)
- [ ] 配置负载均衡

### 高可用

- [ ] 数据库主从复制
- [ ] Redis 哨兵模式
- [ ] 多实例部署
- [ ] 自动故障转移
- [ ] 定期备份策略

## 📞 获取支持

遇到问题？

1. 查看 [部署文档](DEPLOYMENT.md)
2. 查看 [快速开始](QUICKSTART.md)
3. 查看 [README](README.md)
4. 提交 Issue 到 GitHub
5. 联系技术支持

---

**部署清单版本**: 1.0  
**最后更新**: 2026-01-29
