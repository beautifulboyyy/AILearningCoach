# 07_hybrid_deploy_recap.md

## 本次学习目标
在 Windows 环境中，采用“混合部署”运行项目：
- 基础服务放在 Docker（PostgreSQL/Redis/Milvus/MinIO/Etcd）
- 前后端在本机运行，便于 PyCharm Debug 和数据流转观察

## 你本次完成的关键动作
1. 创建并激活 conda 环境，安装后端依赖（`requirements.txt`）。
2. 启动 Docker 基础服务容器，确认端口映射正常。
3. 修改 `.env` 连接配置，使本机后端通过 `localhost` 访问容器服务。
4. 理解并验证 Alembic 迁移状态（数据库版本管理）。
5. 成功执行 `scripts/init_milvus.py`，确认集合存在。
6. 执行 `scripts/create_test_user.py` 时识别“用户已存在”并正确判断为非阻塞问题。
7. 本机启动后端成功（Uvicorn）。
8. 解决前端 `vite` 命令缺失问题：在 `frontend` 目录执行 `npm install`。
9. 前端成功启动并完成登录。

## 关键认知升级（非常重要）
1. `.env` 是项目运行配置的入口。
2. 容器内与本机连接地址不同：
- 容器连容器：用服务名（如 `db`）
- 本机连容器：用 `localhost` + 映射端口
3. `alembic upgrade head` 在新项目里常常就是“初始化/对齐数据库表结构”。
4. 前端和后端一样，都需要本地依赖安装（`npm install` 对应 `pip install`）。

## 本次遇到的问题与处理
1. Alembic 编码报错（`UnicodeDecodeError: gbk`）
- 原因：Windows 默认编码与配置文件编码不一致
- 处理：使用 UTF-8 模式执行 Alembic（你已成功查看 current）

2. 创建测试用户失败（唯一键冲突）
- 报错：`duplicate key value violates unique constraint ix_users_email`
- 原因：测试用户已存在
- 结论：环境可继续，不影响后续运行

3. 前端无法启动（`vite` not found）
- 原因：前端依赖未安装
- 处理：`cd frontend && npm install` 后恢复正常

## 你现在已经具备的能力
1. 独立完成混合部署搭建。
2. 基于日志定位初始化阶段问题。
3. 理解后端迁移与初始化脚本作用。
4. 理解前端依赖管理与启动链路。
5. 能解释“为什么这种部署方式更适合学习与调试”。

## 建议你下一步做什么
1. 在 PyCharm 配置 Backend Debug 断点，跟一次 `/api/v1/chat/stream` 全链路。
2. 补一个小改动并提交（例如聊天错误提示优化），形成“有产出的学习记录”。
3. 每次学习后都补一份简短复盘，持续沉淀为面试素材。

## 可复用命令清单
```powershell
# 启动基础服务（Docker）
docker compose up -d db redis etcd minio milvus-standalone

# 查看状态
docker compose ps

# 数据库迁移（按需）
python -m alembic current
python -m alembic upgrade head

# 初始化 Milvus
python scripts/init_milvus.py

# 启动后端
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动前端
cd frontend
npm install
npm run dev
```
