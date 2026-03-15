# 后续学习计划

这份计划基于当前项目学习进度制定。目标是让学习顺序更贴合工程实际，先补足认证和接口协议，再进入 AI 主链路，最后开始真正做功能迭代。

## 当前进度定位

截至目前，已经完成了：

1. 项目部署与混合运行环境搭建
2. FastAPI 后端基础结构理解
3. 路由、配置、日志、CORS、Nginx 的基础认知
4. PostgreSQL、schema、ORM、Session、CRUD、事务的第一轮学习
5. 读懂大部分 `auth.py` 中数据库相关代码

当前正处于：

从“读懂工程结构”进入“读懂真实业务接口和认证链路”的阶段。

## 第一阶段：以 auth 为核心，学习 HTTP / JWT / 加密

目标：

1. 看懂 [auth.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/auth.py) 全部逻辑
2. 建立后端认证与鉴权的最小知识框架
3. 在真实接口中继续巩固数据库相关知识

重点学习内容：

1. HTTP 基础
2. 请求方法：GET / POST
3. 请求体、响应体、状态码
4. Header 和 Authorization
5. JWT 的结构和作用
6. access token / refresh token
7. 密码哈希和校验
8. FastAPI 里的 `Depends(...)` 和当前用户获取

建议学习顺序：

1. 先读 [app/api/v1/endpoints/auth.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/auth.py)
2. 再读 [app/core/security.py](/D:/Code/python/AILearningCoach/app/core/security.py)
3. 再读 [app/core/deps.py](/D:/Code/python/AILearningCoach/app/core/deps.py)
4. 用 API docs 调试 `/register`、`/login`、`/refresh`、`/me`

阶段成果目标：

1. 能解释注册和登录接口的完整流程
2. 能解释 token 为什么要存在
3. 能解释后端如何识别当前登录用户

## 第二阶段：继续学习主要 API，巩固后端接口开发能力

目标：

1. 读懂项目里其他主要接口模块
2. 建立对业务数据流转的整体感觉

建议优先顺序：

1. `chat`
2. `profile`
3. `task`
4. `progress`
5. `learning_path`

学习方式：

1. 先从 API docs 看接口分组
2. 再读对应 endpoint 文件
3. 再看该接口依赖的 model、schema、service

阶段成果目标：

1. 能解释一个接口从请求到数据库再到响应的流程
2. 能逐步建立项目业务全景

## 第三阶段：结合已有基础，快速学习 AI 相关代码

你的优势：

已经有 langchain 和 OpenAI SDK 经验，所以这部分预计会推进更快。

目标：

1. 理解项目中 Agent、RAG、LLM 调用链路
2. 看懂 AI 能力和后端 API 如何结合

建议学习顺序：

1. [app/ai/agents/orchestrator.py](/D:/Code/python/AILearningCoach/app/ai/agents/orchestrator.py)
2. [app/ai/rag/retriever.py](/D:/Code/python/AILearningCoach/app/ai/rag/retriever.py)
3. [app/ai/rag/generator.py](/D:/Code/python/AILearningCoach/app/ai/rag/generator.py)
4. [app/ai/rag/llm.py](/D:/Code/python/AILearningCoach/app/ai/rag/llm.py)
5. 再回到 [app/api/v1/endpoints/chat.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/chat.py)

阶段成果目标：

1. 能解释聊天接口如何调用 Agent 和 RAG
2. 能解释项目中的大模型应用架构
3. 能把自己的 langchain/OpenAI 经验映射到这个项目

## 第四阶段：寻找未完成功能或可优化点

目标：

1. 从“读懂项目”进入“开始改项目”
2. 把学习成果转化成真正的工程产出

可以做的事情：

1. 找出 README、Roadmap、界面中提到但未完成的功能
2. 找出体验不佳或逻辑不完整的地方
3. 找出可观测性、错误处理、提示信息上的优化机会

优先建议：

1. 先做小改动
2. 再做中等功能
3. 最后再尝试新功能

阶段成果目标：

1. 在项目里提交真实改动
2. 形成可讲的“我做了什么优化”

## 第五阶段：功能迭代和新增功能

目标：

1. 真正以开发者身份参与这个项目
2. 为简历和面试积累“我不仅能读代码，还能迭代代码”的证据

可以尝试的方向：

1. 完善现有功能边界情况
2. 给某个模块补状态提示或错误处理
3. 优化某个接口的返回结构
4. 给 AI 相关模块补一个配置项或调试能力
5. 新增一个小但完整的功能点

阶段成果目标：

1. 能描述一个从需求到实现到测试的改动
2. 能把项目经历从“学习别人的项目”提升成“我做过真实迭代”

## 建议的整体节奏

建议按下面节奏推进：

1. 明天：认证主线，学习 HTTP / JWT / 加密，并结合 `auth.py` 巩固数据库
2. 接下来几天：继续学习主要 API，建立完整后端业务图谱
3. 再往后：集中看 AI 主链路
4. 最后：开始找点做改动和功能迭代

## 每一阶段都建议做的事

为了保证学习能转化成面试能力，建议每阶段都做这三件事：

1. 写一份总结文档
2. 录一次口头讲解或用自己的话复述
3. 做一个最小实践或真实改动

## 这份计划的最终目标

最终目标不是“看完项目”，而是：

1. 能清楚讲出项目架构
2. 能调试主要业务链路
3. 能解释数据库、认证、AI 主链路
4. 能完成至少一到两个真实改动
5. 能把这个项目稳定写进简历并支撑面试追问
