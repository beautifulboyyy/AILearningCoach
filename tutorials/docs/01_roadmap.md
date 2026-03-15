# 分阶段学习路线（4 周）

## Week 1：先把主链路讲清楚
目标：能完整复述“前端发送消息到 AI 返回”的流程。

1. 阅读 [frontend/src/views/chat/ChatView.vue](/D:/Code/python/AILearningCoach/frontend/src/views/chat/ChatView.vue) 与 [frontend/src/stores/chat.ts](/D:/Code/python/AILearningCoach/frontend/src/stores/chat.ts)。
2. 阅读 [frontend/src/api/chat.ts](/D:/Code/python/AILearningCoach/frontend/src/api/chat.ts) 的 SSE 逻辑。
3. 阅读 [app/api/v1/endpoints/chat.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/chat.py) 的 `/chat/stream`。
4. 阅读 [app/ai/agents/orchestrator.py](/D:/Code/python/AILearningCoach/app/ai/agents/orchestrator.py)。

产出：手写一张时序图（用户消息 -> API -> Orchestrator -> Agent -> RAG/LLM -> SSE chunk -> 前端）。

## Week 2：后端分层与数据
目标：理解 API、Service、Model、Schema 的关系和边界。

1. 入口： [main.py](/D:/Code/python/AILearningCoach/main.py) + [app/api/v1/api.py](/D:/Code/python/AILearningCoach/app/api/v1/api.py)。
2. 数据模型：`app/models` 下用户、会话、消息、任务、进度相关模型。
3. 服务层：`app/services`，重点看 `progress_service.py`。
4. 认证：`auth` 路由与 JWT 配置。

产出：画出“一个聊天请求涉及哪些表的读写”。

## Week 3：AI 与 RAG
目标：讲清为什么不是“直接调用一个模型”。

1. LLM 客户端：[app/ai/rag/llm.py](/D:/Code/python/AILearningCoach/app/ai/rag/llm.py)。
2. 检索与生成：[app/ai/rag/retriever.py](/D:/Code/python/AILearningCoach/app/ai/rag/retriever.py) + [app/ai/rag/generator.py](/D:/Code/python/AILearningCoach/app/ai/rag/generator.py)。
3. Agent 层：`qa/planner/analyst/coach` 的职责差异。

产出：准备“RAG、Hybrid retrieval、rerank”的口头解释（1 分钟版）。

## Week 4：部署与可靠性
目标：能解释 docker-compose 每个服务的职责，能排查常见故障。

1. 编排： [docker-compose.yml](/D:/Code/python/AILearningCoach/docker-compose.yml)。
2. 初始化： [scripts/docker_init.sh](/D:/Code/python/AILearningCoach/scripts/docker_init.sh)。
3. 进程入口： [docker-entrypoint.sh](/D:/Code/python/AILearningCoach/docker-entrypoint.sh)。
4. 异步任务： [celery_app.py](/D:/Code/python/AILearningCoach/celery_app.py) + [app/tasks/async_tasks.py](/D:/Code/python/AILearningCoach/app/tasks/async_tasks.py)。

产出：写一份“服务启动失败排查手册（你自己的版本）”。

## 每周固定动作
1. 录一段 3-5 分钟讲解（训练表达）。
2. 提交一个小改动（哪怕是日志、文案、监控字段）。
3. 写一页复盘（问题、解决、收获）。
