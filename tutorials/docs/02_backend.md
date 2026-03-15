# 后端深度学习

## 后端架构（你要会讲）
- 入口层：FastAPI 应用和中间件（[main.py](/D:/Code/python/AILearningCoach/main.py)）。
- 路由层：API endpoint 负责参数和响应（`app/api/v1/endpoints`）。
- 服务层：业务逻辑（`app/services`）。
- 数据层：SQLAlchemy models + async session（`app/models`, `app/db`）。
- AI 层：Agent + RAG（`app/ai`）。

## 聊天接口主流程（最重要）
位置：[app/api/v1/endpoints/chat.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/chat.py)

1. 获取或创建会话 `Conversation`。
2. 落库用户消息 `Message(role=user)`。
3. 读取用户画像与进度，拼装 `context`。
4. 调用 `agent_orchestrator.process` 或 `process_stream`。
5. 落库助手回复 `Message(role=assistant)`。
6. 触发 Celery 异步任务更新画像/进度。

## 你要掌握的设计点
1. 为什么要有 `Service` 层：避免路由层塞满业务逻辑，便于测试。
2. 为什么聊天要有 `session_id`：让多轮对话可追踪、可恢复。
3. 为什么流式接口用 SSE：前端实现简单，适合文本逐段返回。
4. 为什么异步更新画像和进度：降低主请求时延。

## 建议你做的 3 个后端练习
1. 给 `/api/v1/chat/stream` 增加请求追踪 ID（日志里串起来）。
2. 给进度统计接口加一个“最近 7 天消息数”字段。
3. 给健康检查添加更明确的失败原因输出。

## 面试可讲的故障排查例子
- 现象：前端收到 401。
- 排查：请求头 token -> 后端鉴权依赖 -> token 过期策略 -> 登录刷新逻辑。
- 结论：定位为 token 过期未刷新，补充前端拦截器跳转与清理状态。
