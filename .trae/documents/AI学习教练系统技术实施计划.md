## 1. 架构设计 (Layered Architecture)

* **后端 (FastAPI)**: 采用领域驱动设计 (DDD) 思想，划分为 Presentation (API), Application (Service), Domain (Model), Infrastructure (DB/Vector)。

* **前端 (Vue 3)**: 采用模块化管理，状态与视图解耦，重点优化 SSE 流式交互体验。

## 2. 向量化与存储设计 (Vector DB & RAG)

* **选型**: 采用 **Milvus 2.3** 存储向量，使用 **OpenAI** **`text-embedding-3-small`** 进行嵌入。

* **设计**:

  * **静态知识库**: `CourseKnowledge` 集合，采用 HNSW 索引，存储分块讲义。

  * **动态记忆库**: `UserMemories` 集合，按 `user_id` 分区，存储语义化事实碎片。

* **检索策略**: 实现 **混合检索 (Hybrid Search)** + **重排序 (Rerank)**，确保技术回答的专业度与准确性。

## 3. 核心业务系统设计

* **学习路径生成**: 基于用户画像 (JSONB 存储) 的 Prompt Engineering，生成结构化学习树。

* **长期记忆管理**: 异步 Celery 任务执行“事实提取”，对话前自动召回相关记忆。

* **进度追踪**: 建立 `Plan -> Milestone -> Task` 级联模型，支持自动化状态更新。

## 4. 实施路线图

* **Phase 1**: 环境搭建 (PostgreSQL, Milvus, Redis) 与知识库入库脚本开发。

* **Phase 2**: 核心 RAG 对话引擎开发，支持 SSE 流式响应与引用溯源。

* **Phase 3**: 学习计划自动生成逻辑与任务看板 API 实现。

* **Phase 4**: 前端 Vue 3 核心组件开发 (Chat, PathGraph, TaskBoard)。

* **Phase 5**: 记忆系统联调、性能优化与 Docker 容器化部署。

