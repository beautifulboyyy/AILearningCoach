# 后续学习计划

这份计划基于当前真实进度重新调整。

当前你的重点不再是继续平均铺开前后端知识，而是把项目中最有简历价值、最贴近目标岗位的 AI 业务主链路学透，并最终做出真实迭代。

## 当前进度定位

截至目前，你已经完成了：

1. 项目混合部署与运行环境搭建
2. FastAPI 后端基础结构理解
3. 路由、配置、日志、CORS、Nginx 的基础认知
4. PostgreSQL、schema、ORM、Session、CRUD、事务的第一轮学习
5. 注册/登录流程、密码哈希、JWT、Bearer Token 的基础理解
6. 能读懂 `auth.py` 中大部分数据库与认证相关代码

当前所处阶段：

从“能跑项目、能读懂基础后端”进入“重点拆解 AI 业务实现，并逐步形成可讲、可改、可迭代的项目能力”阶段。

## 总体目标

后续学习围绕 4 个核心目标推进：

1. 读懂项目里的 AI 主链路
2. 理解 RAG、Agent、Memory 如何融入真实业务接口
3. 找到一到两个可以真实优化或补全的功能点
4. 最终形成可写进简历、可支撑面试追问的项目经历

## 第一阶段：以 Chat 主链路为核心，学习 AI 业务整体流程

这一阶段是接下来最重要的主线。

目标：

1. 看懂聊天接口如何进入 AI 系统
2. 看懂用户信息、会话、画像、进度如何作为业务上下文进入模型流程
3. 建立“接口层 -> 业务上下文 -> Agent 编排 -> RAG -> LLM -> 返回结果”的全链路认知

建议优先学习的 API 链路：

1. `/api/v1/chat/`
   适合先看非流式版本，链路清晰，便于理解完整调用过程
2. `/api/v1/chat/stream`
   适合第二步学习，理解流式返回、SSE 事件组织与前端展示
3. `/api/v1/agents/intent`
   适合单独学习意图识别和 Agent 路由逻辑
4. `/api/v1/agents/list`
   适合理解当前系统中有哪些 Agent，以及它们的职责分工

建议重点阅读顺序：

1. [chat.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/chat.py)
2. [orchestrator.py](/D:/Code/python/AILearningCoach/app/ai/agents/orchestrator.py)
3. [qa_agent.py](/D:/Code/python/AILearningCoach/app/ai/agents/qa_agent.py)
4. [planner_agent.py](/D:/Code/python/AILearningCoach/app/ai/agents/planner_agent.py)
5. [coach_agent.py](/D:/Code/python/AILearningCoach/app/ai/agents/coach_agent.py)
6. [analyst_agent.py](/D:/Code/python/AILearningCoach/app/ai/agents/analyst_agent.py)

阶段成果目标：

1. 能讲清一次聊天请求是如何进入 AI 系统的
2. 能讲清 orchestrator 在整个系统中的角色
3. 能讲清不同 Agent 的职责边界

## 第二阶段：重点学习 RAG 实现，而不是只看概念 Demo

这部分是你最适合快速突破的内容，因为你已经有 LangChain 和 OpenAI SDK 的经验。

目标：

1. 理解项目里的 RAG 是如何和业务上下文结合的
2. 区分“基础 RAG Demo”和“工程化 RAG 组件”
3. 能解释当前项目 RAG 的复杂度与优缺点

建议重点阅读顺序：

1. [generator.py](/D:/Code/python/AILearningCoach/app/ai/rag/generator.py)
2. [retriever.py](/D:/Code/python/AILearningCoach/app/ai/rag/retriever.py)
3. [llm.py](/D:/Code/python/AILearningCoach/app/ai/rag/llm.py)
4. [bm25.py](/D:/Code/python/AILearningCoach/app/ai/rag/bm25.py)
5. [reranker.py](/D:/Code/python/AILearningCoach/app/ai/rag/reranker.py)
6. [milvus_client.py](/D:/Code/python/AILearningCoach/app/ai/rag/milvus_client.py)

建议配合学习的 API 链路：

1. `/api/v1/chat/` 中技术问答类问题
2. `/api/v1/chat/stream` 中技术问答类问题

阶段成果目标：

1. 能讲清当前项目的检索流程
2. 能说明它是不是 native RAG，是否包含 hybrid retrieve 和 rerank
3. 能说明它与自己做过的 demo 有什么不同

## 第三阶段：学习 Memory 如何落入业务

这一阶段重点不是先背“长期记忆、短期记忆”的理论，而是看项目如何落地。

目标：

1. 看懂当前项目 memory 的数据分层
2. 看懂哪些能力已经实现，哪些还只是基础设施
3. 区分记忆系统与聊天主链路的集成深度

建议重点阅读顺序：

1. [manager.py](/D:/Code/python/AILearningCoach/app/ai/memory/manager.py)
2. [compressor.py](/D:/Code/python/AILearningCoach/app/ai/memory/compressor.py)
3. [memory.py](/D:/Code/python/AILearningCoach/app/models/memory.py)
4. [memory.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/memory.py)

建议配合学习的 API 链路：

1. `/api/v1/memory/`
2. `/api/v1/memory/search`
3. `/api/v1/memory/export`

阶段成果目标：

1. 能讲清当前项目的短期记忆、工作记忆、长期记忆分别存在哪里
2. 能说明记忆系统是否已经深度接入聊天主流程
3. 能识别后续是否适合把 memory 真正接入 chat 上下文

## 第四阶段：回到业务接口，学习 AI 与后端业务如何融合

前面三阶段主要是在拆 AI 内核，这一阶段要重新回到“业务项目”的视角。

目标：

1. 看懂 AI 输出如何影响用户画像、学习进度、会话记录
2. 看懂异步任务和 AI 业务之间的关系
3. 从“会看 AI 代码”升级到“会看 AI 业务系统”

建议重点阅读：

1. [chat.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/chat.py)
2. [profile.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/profile.py)
3. [progress.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/progress.py)
4. `app/tasks/async_tasks.py`
5. `app/services/progress_service.py`
6. `app/services/profile_service.py`

阶段成果目标：

1. 能讲清 AI 结果为什么不只是“回答问题”
2. 能讲清这个项目如何把对话沉淀为业务数据
3. 能讲清异步任务在这个项目中的意义

## 第五阶段：找可优化点，开始真实迭代

这一阶段开始从学习者切换成贡献者。

目标：

1. 找出项目中未完全实现的功能
2. 找出可以增强的 AI 业务点
3. 在项目中做真实改动

优先建议寻找的方向：

1. Memory 与 chat 主链路的集成不足
2. Agent 工具能力虽然有抽象，但当前可能未真正使用
3. RAG 的检索结果使用方式是否还能增强
4. Prompt、日志、可观测性、错误提示是否还可优化
5. 是否可以补一个更完整的 learning coach 工作流

阶段成果目标：

1. 在项目里做出一到两个可讲的真实优化
2. 形成“我不只是看懂了，还做了改进”的项目故事

## 第六阶段：尝试新增一个 AI 业务功能

当你对现有链路已经比较熟时，再尝试新增功能。

建议方向：

1. 将 Memory 真正接入聊天上下文
2. 给 Agent 增加真实工具调用
3. 增加更强的学习规划工作流
4. 给 RAG 增加更丰富的过滤条件或引用展示

阶段成果目标：

1. 能完整讲清一个新增功能从需求到实现的过程
2. 让项目经历更像“真实开发经历”而不只是“学习别人项目”

## 建议的实际推进顺序

建议按下面节奏推进：

1. 先完成 login/auth 的总结收尾
2. 接下来 2 到 4 天重点盯住 `chat -> orchestrator -> agent -> rag`
3. 然后单独抽一轮学习 memory
4. 再回到 profile、progress、async tasks 看 AI 如何落地成业务
5. 最后开始找优化点和可迭代功能

## 每一阶段都建议做的三件事

为了让学习真正转化成面试能力，建议每一阶段都做：

1. 写一份总结文档
2. 用自己的话口头讲一次这条链路
3. 至少做一次真实调试、修改或实验

## 这份计划的最终目标

最终目标不是“把项目每个文件都看完”，而是：

1. 能讲清项目中的 AI 主链路
2. 能解释 RAG、Agent、Memory 在业务中的角色
3. 能指出项目当前实现的复杂度、优点和边界
4. 能做出真实改动并写进简历
5. 能在面试里把这个项目讲成一段完整的 AI 应用开发经历
