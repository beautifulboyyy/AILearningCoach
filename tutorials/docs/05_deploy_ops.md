# 部署与运维学习

## docker-compose 服务角色
文件：[docker-compose.yml](/D:/Code/python/AILearningCoach/docker-compose.yml)

1. `db`：PostgreSQL 业务数据。
2. `redis`：缓存与 Celery broker/backend。
3. `etcd/minio/milvus-standalone`：向量数据库依赖。
4. `init`：初始化数据库、Milvus、测试用户。
5. `app`：FastAPI 主服务。
6. `celery_worker`：异步任务消费。
7. `celery_beat`：定时任务调度。
8. `frontend`：Nginx 托管前端并反向代理 API。

## 启动顺序（关键）
- 基础服务先健康。
- `init` 完成后写入初始化标记。
- `app/worker/beat` 通过 entrypoint 等待初始化标记再启动。

关键文件：
- [scripts/docker_init.sh](/D:/Code/python/AILearningCoach/scripts/docker_init.sh)
- [docker-entrypoint.sh](/D:/Code/python/AILearningCoach/docker-entrypoint.sh)
- [Dockerfile](/D:/Code/python/AILearningCoach/Dockerfile)

## 常见故障排查
1. 前端打不开：看 `frontend` 容器健康与端口 3000。
2. 接口 500：看 `app` 日志、`.env` 的 API key/数据库配置。
3. 聊天无回答：查 LLM key、外网访问、Milvus 可用性。
4. 异步任务没执行：看 `celery_worker` 是否在线，broker 连接是否正常。
5. 初始化卡住：看 `init` 容器日志是否在等 db/redis/milvus。

## 运维面试表达
- 我不只会“docker compose up”，还理解了依赖顺序、健康检查、初始化流程和异步任务拓扑。
- 出问题时会从网关、应用、依赖服务三层逐步定位。
