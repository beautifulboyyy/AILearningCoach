# AI Learning Coach 学习总览（面试导向）

这套教程的目标是让你从“会部署”升级到“能讲清设计、能定位问题、能做小改动并复盘”。

## 你现在的进度
- 已完成：Windows + Docker Desktop 成功部署并进入前端页面。
- 下一步：系统学习前端、后端、AI/RAG、部署与异步任务。

## 项目一句话（简历可用）
一个基于 `FastAPI + Vue3 + Multi-Agent + RAG + Milvus + Celery + Docker` 的 AI 学习教练系统，支持流式对话、学习路径规划、学习进度分析和任务管理。

## 核心入口文件（先建立地图）
- [main.py](/D:/Code/python/AILearningCoach/main.py)
- [app/api/v1/api.py](/D:/Code/python/AILearningCoach/app/api/v1/api.py)
- [app/api/v1/endpoints/chat.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/chat.py)
- [app/ai/agents/orchestrator.py](/D:/Code/python/AILearningCoach/app/ai/agents/orchestrator.py)
- [app/ai/rag/generator.py](/D:/Code/python/AILearningCoach/app/ai/rag/generator.py)
- [app/ai/rag/retriever.py](/D:/Code/python/AILearningCoach/app/ai/rag/retriever.py)
- [app/ai/rag/llm.py](/D:/Code/python/AILearningCoach/app/ai/rag/llm.py)
- [app/tasks/async_tasks.py](/D:/Code/python/AILearningCoach/app/tasks/async_tasks.py)
- [frontend/src/views/chat/ChatView.vue](/D:/Code/python/AILearningCoach/frontend/src/views/chat/ChatView.vue)
- [frontend/src/api/chat.ts](/D:/Code/python/AILearningCoach/frontend/src/api/chat.ts)
- [docker-compose.yml](/D:/Code/python/AILearningCoach/docker-compose.yml)

## 推荐学习顺序
1. 先打通一条“消息链路”。
2. 再理解后端分层与数据模型。
3. 再理解 AI 层（意图识别、Agent 路由、RAG）。
4. 最后掌握部署、健康检查、异步任务。

## 本目录文档
- [01_roadmap.md](/D:/Code/python/AILearningCoach/tutorials/01_roadmap.md)
- [02_backend.md](/D:/Code/python/AILearningCoach/tutorials/02_backend.md)
- [03_frontend.md](/D:/Code/python/AILearningCoach/tutorials/03_frontend.md)
- [04_llm_rag.md](/D:/Code/python/AILearningCoach/tutorials/04_llm_rag.md)
- [05_deploy_ops.md](/D:/Code/python/AILearningCoach/tutorials/05_deploy_ops.md)
- [06_resume_interview.md](/D:/Code/python/AILearningCoach/tutorials/06_resume_interview.md)
