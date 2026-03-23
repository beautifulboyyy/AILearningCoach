# DeepResearch 后端设计文档

**日期：** 2026-03-23  
**状态：** 待评审  
**范围：** 仅后端第一版，不包含前端页面与 SSE 实时推送  

## 1. 背景与目标

当前项目已经具备基于 FastAPI、SQLAlchemy、Celery 和多类 AI 服务的后端框架，但现有 `/chat` 接口的职责是单轮或短链路问答，不适合承载耗时较长、包含多阶段状态流转和人工反馈环节的深度研究（Deep Research）能力。

项目中已有一个原型实现 [`research_assistant.py`](D:/Code/python/AILearningCoach/research_assistant.py)，其中包含分析师生成、访谈、检索、报告整合和人机协同的基础思路。第一版目标不是将该原型直接并入现有聊天接口，而是基于当前项目框架，抽象出一套独立的 DeepResearch 后端能力。

第一版目标如下：

- 提供独立于 `/chat` 的 DeepResearch 后端接口。
- 采用异步任务模式，支持长耗时研究流程。
- 将研究记录长期保存，用户可反复查看。
- 支持分析师草案的有限多轮自然语言反馈。
- 在分析师确认后启动正式研究流程。
- 第一版只实现后端，不实现前端页面和 SSE 推送。

## 2. 不在本期范围内

为控制第一版复杂度，以下内容明确不纳入本期：

- 不复用现有聊天会话模型和聊天接口语义。
- 不支持用户逐字段手工编辑分析师对象。
- 不支持在研究正式启动后继续修改分析师。
- 不支持无限轮反馈，第一版限制最多 3 轮。
- 不实现 SSE 或 WebSocket 实时进度推送，前端先通过轮询获取状态。
- 不做完整的 LangGraph checkpoint 持久化恢复。
- 不做报告导出 PDF、分享链接、公开链接等扩展能力。

## 3. 需求概述

### 3.1 用户需求

用户希望围绕某个研究主题发起一个独立的 DeepResearch 任务，而不是在普通聊天里进行。系统先自动生成一组分析师草案，用户可以通过自然语言提交反馈，要求系统调整分析师视角。经过有限轮调整后，用户确认分析师阵容，再由后端异步完成正式研究并产出最终报告。研究完成后，记录长期保存，用户之后可以再次查看。

### 3.2 核心能力

- 创建研究任务。
- 生成分析师草案。
- 提交自然语言反馈并重新生成分析师草案。
- 确认当前分析师版本并启动正式研究。
- 查询研究任务列表与详情。
- 获取最终研究报告。
- 保存研究状态、分析师版本历史、正式研究结果与错误信息。

## 4. 设计原则

- **独立边界：** DeepResearch 作为独立业务域设计，不挤入现有 `/chat` 链路。
- **先稳后全：** 第一版优先实现稳定的业务状态机，不依赖复杂的工作流恢复机制。
- **有限交互：** 人工反馈只发生在分析师确认前，正式研究开始后冻结输入。
- **长期保存：** 研究任务、分析师版本、最终报告均持久化。
- **可扩展：** 后续可以继续扩展 SSE 推送、报告导出、更多人工干预节点。

## 5. 总体方案

### 5.1 方案结论

第一版采用“业务状态机 + 双 Celery 任务”的实现方案，而不是直接依赖 LangGraph 原生的中断恢复能力。

核心做法如下：

- 将流程拆成两个阶段：
  - 分析师草案阶段
  - 正式研究阶段
- 每个阶段由独立的 Celery 任务驱动。
- 人工反馈环节由数据库状态机承接。
- LangGraph 逻辑拆为两个可独立调用的服务入口：
  - `generate_analysts(...)`
  - `run_research(...)`

### 5.2 为什么不采用原型里的单图中断恢复

原型中的 `human_feedback` 节点适合 Demo，但在当前项目第一版中直接落地会引入较高的工程复杂度，主要包括：

- 需要稳定的 graph checkpoint 持久化机制。
- 需要管理 graph resume key、thread id 和状态兼容。
- 错误恢复、版本迭代和排障成本更高。

相比之下，业务状态机方案更契合当前项目已经存在的 FastAPI + Celery 架构，也更适合在仅做后端第一版时快速形成闭环。

## 6. 业务流程

### 6.1 主流程

1. 用户发起 DeepResearch 任务。
2. 系统创建研究记录，状态进入 `drafting_analysts`。
3. Celery 异步生成第一版分析师草案。
4. 任务进入 `waiting_feedback`，用户查看草案。
5. 用户可执行以下两类动作：
   - 提交自然语言反馈，重新生成分析师草案。
   - 确认当前分析师版本，启动正式研究。
6. 一旦启动正式研究，系统锁定当前分析师版本，状态进入 `running_research`。
7. Celery 异步执行正式研究，生成最终报告。
8. 成功后任务状态进入 `completed`；失败则进入 `failed`。

### 6.2 多轮反馈机制

第一版采用“有限多轮、整体重生成”的方式，而不是“自由编辑分析师对象”。

规则如下：

- 最多允许 3 轮反馈。
- 每轮反馈只接受一段自然语言。
- 每轮反馈基于当前任务上下文重新生成一组分析师草案。
- 用户不能直接修改分析师的字段值。
- 正式研究开始后，不再允许修改分析师。

这种设计可以在保留人机协同价值的同时，显著降低前后端复杂度。

## 7. 状态机设计

### 7.1 任务状态

建议定义以下主状态：

| 状态值 | 含义 |
|---|---|
| `pending` | 任务已创建，尚未进入执行 |
| `drafting_analysts` | 正在生成分析师草案 |
| `waiting_feedback` | 分析师草案已生成，等待用户反馈或确认 |
| `running_research` | 已确认分析师，正在执行正式研究 |
| `completed` | 研究已完成 |
| `failed` | 执行失败 |
| `cancelled` | 用户取消或系统终止 |

### 7.2 阶段字段

除主状态外，建议增加更细粒度的 `phase` 字段，便于前端轮询展示：

| phase | 含义 |
|---|---|
| `analyst_generation` | 分析师生成中 |
| `analyst_feedback` | 等待分析师反馈 |
| `research_execution` | 正式研究执行中 |
| `report_finalization` | 正在整合最终报告 |

### 7.3 状态流转

```text
pending
  -> drafting_analysts
  -> waiting_feedback
    -> drafting_analysts      (提交反馈后重新生成)
    -> running_research       (确认并启动研究)
  -> completed
  -> failed
  -> cancelled
```

## 8. 数据模型设计

第一版建议至少新增 3 张业务表，而不是将所有信息塞进一张表中。

### 8.1 `deep_research_tasks`

用于保存任务主记录。

建议字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 主键 |
| `user_id` | int | 关联用户 |
| `topic` | varchar | 研究主题 |
| `requirements` | text / json | 用户补充要求，可为空 |
| `status` | enum | 主状态 |
| `phase` | enum / varchar | 当前阶段 |
| `progress_percent` | int | 进度百分比 |
| `progress_message` | varchar | 当前进度文案 |
| `current_revision` | int | 当前分析师版本号 |
| `max_feedback_rounds` | int | 最大反馈轮数，默认 3 |
| `selected_revision` | int | 被确认用于正式研究的版本号，可为空 |
| `final_report_markdown` | long text | 最终 Markdown 报告 |
| `final_report_summary` | text | 报告摘要，可选 |
| `error_message` | text | 失败原因 |
| `started_at` | datetime | 正式研究开始时间 |
| `completed_at` | datetime | 完成时间 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

职责：

- 作为任务列表和详情页的主数据源。
- 提供当前状态、阶段、当前版本和最终结果。

### 8.2 `deep_research_analyst_revisions`

用于保存每一轮分析师草案。

建议字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 主键 |
| `task_id` | int | 所属任务 |
| `revision_number` | int | 版本号，从 1 开始 |
| `feedback_text` | text | 本轮生成前的反馈内容，首轮可为空 |
| `analysts_json` | json / text | 当前版本分析师列表 |
| `is_selected` | bool | 是否被最终选定 |
| `created_at` | datetime | 创建时间 |

职责：

- 保存分析师草案的完整版本历史。
- 支撑用户回看每一轮分析师调整结果。
- 为正式研究提供最终被锁定的分析师输入。

### 8.3 `deep_research_runs`

用于保存正式研究执行记录。

建议字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 主键 |
| `task_id` | int | 所属任务 |
| `revision_number` | int | 使用的分析师版本号 |
| `status` | enum | 执行状态 |
| `progress_percent` | int | 执行进度 |
| `progress_message` | varchar | 执行进度文案 |
| `result_json` | json / text | 中间产物或最终结构化结果 |
| `error_message` | text | 执行异常信息 |
| `started_at` | datetime | 开始时间 |
| `finished_at` | datetime | 结束时间 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

职责：

- 记录正式研究阶段的执行轨迹。
- 为后续支持重跑、审计和中间结果查看预留空间。

## 9. API 设计

第一版建议新增独立路由组：`/api/v1/deepresearch`

### 9.1 创建任务

`POST /deepresearch/tasks`

用途：

- 创建研究任务。
- 初始化主记录。
- 投递分析师草案生成任务。

请求体建议：

```json
{
  "topic": "如何设计面向成人学习者的 AI 编程教练系统",
  "requirements": "更关注产品结构、技术实现和用户留存",
  "max_analysts": 4
}
```

响应体建议：

```json
{
  "id": 101,
  "status": "drafting_analysts",
  "phase": "analyst_generation",
  "progress_percent": 5,
  "progress_message": "正在生成分析师草案"
}
```

### 9.2 获取任务列表

`GET /deepresearch/tasks`

用途：

- 获取用户自己的 DeepResearch 历史列表。
- 支持按状态筛选和分页。

### 9.3 获取任务详情

`GET /deepresearch/tasks/{id}`

用途：

- 获取任务当前状态、当前分析师草案、剩余反馈次数、当前报告摘要等信息。

建议响应字段包括：

- 任务基础信息
- 当前状态与阶段
- 当前分析师版本
- 当前分析师列表
- 当前反馈轮次
- 剩余反馈次数
- 最终报告是否可用
- 错误信息

### 9.4 提交反馈

`POST /deepresearch/tasks/{id}/feedback`

用途：

- 在 `waiting_feedback` 状态下提交自然语言反馈。
- 创建新一轮分析师生成任务。

请求体建议：

```json
{
  "feedback": "减少宏观产业视角，增加具体教学设计和技术架构分析"
}
```

接口约束：

- 只有 `waiting_feedback` 状态可调用。
- 超过最大反馈轮数时返回业务错误。
- 已进入 `running_research`、`completed` 或 `failed` 状态时不可调用。

### 9.5 启动正式研究

`POST /deepresearch/tasks/{id}/start`

用途：

- 确认当前分析师版本。
- 锁定分析师阵容。
- 投递正式研究 Celery 任务。

接口约束：

- 只有 `waiting_feedback` 状态可调用。
- 必须存在当前有效分析师版本。

### 9.6 获取报告

`GET /deepresearch/tasks/{id}/report`

用途：

- 返回最终 Markdown 报告全文。
- 如果任务尚未完成，则返回明确状态提示。

## 10. 模块边界设计

### 10.1 API 层

建议新增：

- `app/api/v1/endpoints/deepresearch.py`

职责：

- 接收请求和做权限校验。
- 调用 service 层完成业务操作。
- 返回统一响应结构。

### 10.2 Schema 层

建议新增：

- `app/schemas/deepresearch.py`

职责：

- 定义创建任务、提交反馈、任务详情、报告响应等 Pydantic 模型。

### 10.3 Model 层

建议新增：

- `app/models/deepresearch.py`

职责：

- 定义 DeepResearch 相关 ORM 模型和枚举。

### 10.4 Service 层

建议新增：

- `app/services/deepresearch_service.py`
- `app/services/deepresearch_runner.py`

职责拆分：

- `deepresearch_service.py`
  - 负责业务状态机。
  - 负责数据读写、校验、状态流转。
  - 负责投递 Celery 任务。
- `deepresearch_runner.py`
  - 负责调用 AI 工作流。
  - 封装 `generate_analysts(...)` 和 `run_research(...)` 两个主要入口。

### 10.5 AI 工作流层

建议新增目录：

- `app/ai/deepresearch/`

可拆分为：

- `workflow.py`
- `prompts.py`
- `models.py`
- `search.py`
- `formatters.py`

职责：

- 承接从原型中迁移出来的 LangGraph / LLM / 搜索逻辑。
- 与 API、数据库、Celery 解耦。

### 10.6 Task 层

建议新增：

- `app/tasks/deepresearch_tasks.py`

建议包含两个主要 Celery 任务：

- `generate_analysts_task(task_id: int)`
- `run_deepresearch_task(task_id: int)`

## 11. AI 工作流改造方案

### 11.1 从原型中迁移的核心内容

原型中可以保留并迁移的核心能力包括：

- 分析师数据模型
- 分析师草案生成逻辑
- 访谈子图
- 检索与回答逻辑
- section 生成逻辑
- 最终报告整合逻辑

### 11.2 需要改造的部分

原型中以下设计需要调整：

1. 不直接使用 `human_feedback` 作为 graph 内部交互节点。
2. 不依赖 `MemorySaver` 作为长期持久化方案。
3. 不将第一版交互恢复能力建立在 graph checkpoint 上。
4. 将工作流拆分为两个清晰的服务入口：

```python
generate_analysts(topic, requirements, max_analysts, feedback_history)
run_research(topic, selected_analysts, run_context)
```

### 11.3 为什么拆成两个入口

这样拆分后：

- 分析师阶段是短任务，容易重试。
- 正式研究阶段是长任务，职责单一。
- 中间由业务状态机承接人工反馈，更符合项目当前后端架构。

## 12. 进度与错误处理

### 12.1 进度展示

第一版不实现 SSE，但应在数据库中维护基础进度信息，供前端轮询展示。

建议维护以下字段：

- `progress_percent`
- `progress_message`

示例文案：

- `正在生成分析师草案`
- `已生成 4 位分析师，等待你的反馈`
- `正在进行第 2/4 位分析师访谈`
- `正在整合研究结果`
- `报告已生成`

### 12.2 错误处理

当任务失败时：

- 主任务状态更新为 `failed`
- 写入 `error_message`
- 对正式研究阶段的失败，同步更新 `deep_research_runs`
- 保留已经生成的分析师版本和历史记录，便于排障和后续重试

## 13. 权限与安全

第一版沿用现有用户鉴权机制：

- 只有登录用户可访问 DeepResearch 接口。
- 用户只能访问自己的 research 任务。
- `task_id` 查询必须始终附带 `user_id` 约束。

另外建议：

- 限制 topic 与 feedback 的最大长度，防止超长输入。
- 对正式研究任务设置 Celery 超时与重试策略。
- 对外部搜索失败做降级处理，避免单点失败导致整个任务不可用。

## 14. 测试策略

第一版建议覆盖以下层次的测试。

### 14.1 单元测试

覆盖内容：

- 状态机流转校验
- 反馈轮数限制
- 任务启动条件校验
- 任务详情序列化

### 14.2 集成测试

覆盖内容：

- 创建任务后是否成功投递分析师任务
- 提交反馈后是否正确生成新 revision
- 启动正式研究后是否锁定 selected revision
- 正式研究完成后是否正确落库报告

### 14.3 API 测试

覆盖内容：

- 鉴权校验
- 只能访问自己的任务
- 非法状态下调用 `feedback/start` 的错误响应
- 未完成任务获取报告时的返回行为

## 15. 演进路线

在第一版稳定后，可继续考虑以下扩展：

- 增加 SSE 进度推送。
- 支持报告导出为 PDF 或富文本。
- 支持报告分享和历史版本比较。
- 为正式研究阶段增加更细的中间产物可视化。
- 评估是否需要引入 LangGraph 持久化 checkpoint，以支持更多人工干预节点。

## 16. 推荐实施顺序

建议按如下顺序实施：

1. 建立数据模型与 Alembic 迁移。
2. 建立 Schema 和 Service。
3. 增加 DeepResearch API 路由。
4. 抽离原型中的分析师生成逻辑。
5. 接入分析师 Celery 任务。
6. 接入正式研究 Celery 任务。
7. 补齐任务详情和报告查询接口。
8. 补充单元测试、集成测试和 API 测试。

## 17. 结论

DeepResearch 第一版应作为独立业务域实现，而不是并入现有聊天接口。实现上采用“业务状态机 + 双 Celery 任务 + 持久化版本记录”的方案，可以在控制复杂度的前提下，支持分析师草案的有限多轮自然语言反馈，并满足长期保存研究记录的产品目标。

该方案与当前项目现有的 FastAPI、SQLAlchemy 和 Celery 结构高度兼容，能够以较低风险完成第一版后端落地，同时为后续的 SSE 进度推送、更多人工干预节点和报告能力扩展保留清晰的演进空间。
