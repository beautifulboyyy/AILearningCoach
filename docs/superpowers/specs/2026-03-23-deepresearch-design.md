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
- **搜索固定化：** 第一版搜索层固定采用 Tavily API 与博查 API 双供应商方案，不做通用多供应商抽象。
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

- 首版分析师草案 `revision_number = 1`，它是系统初始生成结果，不计入反馈轮次。
- 最多允许 3 轮反馈，指最多允许 3 次成功调用反馈接口并生成新 revision。
- 每轮反馈只接受一段自然语言。
- 每轮反馈基于当前任务上下文重新生成一组分析师草案。
- 用户不能直接修改分析师的字段值。
- 正式研究开始后，不再允许修改分析师。

这种设计可以在保留人机协同价值的同时，显著降低前后端复杂度。

### 6.3 反馈计数规则

为避免前后端、数据库和任务逻辑出现 off-by-one，第一版明确采用以下计数口径：

- `revision_number = 1` 表示初始草案，不计入反馈轮次。
- 每次 `POST /deepresearch/tasks/{id}/feedback` 成功受理后，都会创建一个新的 analyst revision，并使 `feedback_round_used += 1`。
- `feedback_round_used` 的计算公式为：`current_revision - 1`。
- `remaining_feedback_rounds` 的计算公式为：`max_feedback_rounds - feedback_round_used`。
- 当 `feedback_round_used >= max_feedback_rounds` 时，禁止再次提交反馈。
- 详情接口返回的“当前反馈轮次”字段，统一表示 `feedback_round_used`，而不是 `current_revision`。

示例：

- 初始生成完成后：`current_revision = 1`，`feedback_round_used = 0`，`remaining_feedback_rounds = 3`
- 第 1 次反馈完成后：`current_revision = 2`，`feedback_round_used = 1`，`remaining_feedback_rounds = 2`
- 第 3 次反馈完成后：`current_revision = 4`，`feedback_round_used = 3`，`remaining_feedback_rounds = 0`

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
```

说明：

- 第一版不支持显式取消任务，因此不在可达状态中保留 `cancelled`。
- 如后续需要增加取消能力，应同时补充取消接口、worker 协作式停止规则和结果写回约束，再将 `cancelled` 状态引入状态机。

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
| `feedback_round_used` | int | 已使用反馈轮次，公式为 `current_revision - 1` |
| `max_feedback_rounds` | int | 最大反馈轮数，默认 3 |
| `selected_revision` | int | 被确认用于正式研究的版本号，可为空；它是“最终选中 revision”的唯一权威字段 |
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
- 提供反馈轮次与剩余反馈次数的统一口径。
- 作为“当前被锁定用于正式研究的 revision”的唯一权威来源。

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
- `is_selected` 只是冗余展示字段，不能替代 `deep_research_tasks.selected_revision` 作为权威来源。

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
- 当前反馈轮次（`feedback_round_used`）
- 剩余反馈次数（`remaining_feedback_rounds`）
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
- `feedback_round_used < max_feedback_rounds` 时才可调用。
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

### 9.7 并发限制

为控制队列占用和模型成本，第一版在创建任务接口增加用户级并发限制：

- 同一用户在任意时刻最多只允许存在 1 个处于 `drafting_analysts` 或 `running_research` 状态的任务。
- 如果用户已有进行中的 DeepResearch 任务，`POST /deepresearch/tasks` 返回业务错误。
- `waiting_feedback` 状态不计入运行中并发，因为此时不占用后台执行资源。
- 后续如需要放宽限制，可扩展为按用户套餐或角色配置。

仅有“先查询再拒绝”的应用层校验并不足够，第一版必须增加数据库级或事务级防并发方案，防止两个并发创建请求同时穿透限制。

建议实现约束如下：

- `create_task` 必须在事务中执行。
- 在同一事务内，对“当前用户”做并发串行化保护，至少满足以下两种方式之一：
  - 对用户维度加锁（例如基于用户行的 `SELECT ... FOR UPDATE`，或专门的用户级占位锁记录）
  - 引入可落地的唯一约束 / 锁表机制，确保同一用户同一时刻最多只能成功创建一个运行中任务
- 不接受单纯“先查 running task，再 insert”且无锁的实现。
- 若事务提交时发现约束冲突，应返回明确的业务错误，而不是产生两条同时运行的任务。

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

### 10.6 搜索层约束

第一版搜索层不做“任意搜索供应商可插拔”设计，而是明确固定为以下双供应商：

- Tavily API
- 博查 API

设计要求如下：

- `.env` 中显式配置：
  - `TAVILY_API_KEY`
  - `BOCHA_API_KEY`
- 由 `app/ai/deepresearch/search.py` 统一封装两个搜索客户端。
- 搜索适配层对上只暴露项目内部统一的数据结构，不向 runner 透出供应商差异。
- 第一版建议优先查询 Tavily，再查询博查；也可以并发查询后在适配层统一归并，但必须在实现时固定策略，避免线上行为不一致。
- 供应商返回结果在进入 workflow 前统一转换为标准结构，例如：
  - `title`
  - `url`
  - `content`
  - `source`
  - `provider`
- 若单一供应商失败，允许使用另一供应商结果继续执行。
- 若两个供应商都失败，允许研究流程降级继续，但必须记录 warning，并在相关 section / report 生成中处理空来源场景。

### 10.7 Task 层

建议新增：

- `app/tasks/deepresearch_tasks.py`

建议包含两个主要 Celery 任务：

- `generate_analysts_task(task_id: int, expected_revision: int, expected_status: str)`
- `run_deepresearch_task(task_id: int, selected_revision: int, expected_status: str)`

所有 Celery 任务都必须遵循“显式版本绑定 + 预期状态校验 + stale task 丢弃”原则，不能只依赖 `task_id` 执行。

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

5. 将原型中的单一 Web 搜索逻辑替换为 Tavily API 与博查 API 的双搜索源适配层。

### 11.3 为什么拆成两个入口

这样拆分后：

- 分析师阶段是短任务，容易重试。
- 正式研究阶段是长任务，职责单一。
- 中间由业务状态机承接人工反馈，更符合项目当前后端架构。

### 11.4 搜索执行策略

第一版明确采用固定搜索策略，而不是由实现者临时决定：

- analyst 访谈中的搜索请求统一通过 `DeepResearchSearchService` 发起。
- 服务内部接入 Tavily API 与博查 API。
- 默认策略建议为：
  - 先调用 Tavily
  - 再调用博查
  - 将结果按 URL 去重后合并
  - 截断到 workflow 需要的最大来源数
- 每条来源都保留 `provider` 字段，便于日志、排障和后续效果分析。
- 两个供应商都失败时，workflow 继续执行，但会在任务日志和 run 记录中留下搜索降级痕迹。

## 12. Celery 幂等与过期任务防护

第一版必须把 Celery 的重复投递、人工重试、worker 重启后重复消费视为常态，而不是异常。所有异步任务都需要具备幂等性和过期任务防护能力。

### 12.1 任务参数要求

建议任务签名如下：

```python
generate_analysts_task(
    task_id: int,
    expected_revision: int,
    expected_status: str = "drafting_analysts",
)

run_deepresearch_task(
    task_id: int,
    selected_revision: int,
    expected_status: str = "running_research",
)
```

参数语义如下：

- `task_id`：业务任务主键。
- `expected_revision`：本次 analyst 生成任务预期要产出的 revision 编号。
- `selected_revision`：正式研究绑定的 analyst 版本，启动后不可漂移。
- `expected_status`：任务开始执行前要求数据库主记录所处的状态。

### 12.2 Analyst 生成任务的校验规则

`generate_analysts_task` 执行前必须校验：

- 当前任务状态仍为 `drafting_analysts`
- 当前任务的 `current_revision + 1 == expected_revision`，或者在刚创建任务时满足“下一版待生成”的约定
- 任务尚未 `completed` 或 `failed`

执行完成准备写回时，必须再次做 compare-and-set 式校验：

- 目标任务仍处于本次任务可写回的状态
- 数据库中的 revision 游标没有被更新到更新的版本

如果任一校验失败，则将该 Celery 任务标记为 `stale task` 并直接丢弃，不写回数据库，不覆盖新状态。

### 12.3 正式研究任务的校验规则

`run_deepresearch_task` 执行前必须校验：

- 当前任务状态仍为 `running_research`
- 当前任务的 `selected_revision == selected_revision`
- 对应 revision 的 analyst 数据存在且已被锁定

执行完成准备写回时，必须再次校验：

- 任务仍处于 `running_research`
- `selected_revision` 未被修改

如校验失败，视为 `stale task`，不得写回最终报告或覆盖错误状态。

### 12.4 幂等语义

第一版要求以下行为具备幂等性：

- 同一个 analyst 生成任务重复消费时，最多只生成并写回 1 次目标 revision。
- 同一个正式研究任务重复消费时，最多只写回 1 次最终报告。
- 已完成的任务重复执行时，必须安全退出，不得重复覆盖完成结果。

### 12.5 服务层配合要求

为支持 Celery 幂等与 stale task 丢弃，service 层需要提供显式的原子更新方法，例如：

- 按 `task_id + expected_status + expected_revision` 更新状态
- 按 `task_id + selected_revision` 锁定正式研究输入
- 写回前再次比较当前任务状态与 revision
- 在 `create_task` 中对用户维度执行事务级并发保护，避免“双创建请求同时通过”的竞态

实现层可使用数据库事务、行级锁或 compare-and-set 风格的条件更新语句来保证一致性。

## 13. Selected Revision 一致性规则

第一版必须避免 `deep_research_tasks.selected_revision` 与 `deep_research_analyst_revisions.is_selected` 形成“双重真相”。

规则如下：

- `deep_research_tasks.selected_revision` 是“当前最终选中 revision”的唯一权威字段。
- `deep_research_analyst_revisions.is_selected` 只是冗余展示字段，用于详情接口和审计展示。
- 任何读取“当前被选中的 analyst revision”时，应优先读取 `deep_research_tasks.selected_revision`，再回查对应 revision 记录。
- 不允许仅更新 `is_selected` 而不更新 `selected_revision`。
- 不允许通过查询 `is_selected = true` 来反推出当前任务的权威选中版本。

启动正式研究时，必须在同一事务内完成以下操作：

1. 校验当前任务状态为 `waiting_feedback`
2. 校验目标 `revision_number` 存在
3. 将任务表的 `selected_revision` 更新为目标 revision
4. 将该任务下其他 revision 的 `is_selected` 批量置为 `false`
5. 将目标 revision 的 `is_selected` 置为 `true`
6. 将任务状态推进到 `running_research`

事务完成后，必须满足：

- 同一任务最多只有一条 revision 记录满足 `is_selected = true`
- 若 `selected_revision` 非空，则必然存在且仅存在一个 matching revision 的 `is_selected = true`
- 若发生事务失败，则两者都不应部分更新

## 14. 进度与错误处理

### 14.1 进度展示

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

### 14.2 错误处理

当任务失败时：

- 主任务状态更新为 `failed`
- 写入 `error_message`
- 对正式研究阶段的失败，同步更新 `deep_research_runs`
- 保留已经生成的分析师版本和历史记录，便于排障和后续重试

## 15. 权限与安全

第一版沿用现有用户鉴权机制：

- 只有登录用户可访问 DeepResearch 接口。
- 用户只能访问自己的 research 任务。
- `task_id` 查询必须始终附带 `user_id` 约束。

另外建议：

- 限制 topic 与 feedback 的最大长度，防止超长输入。
- 对正式研究任务设置 Celery 超时与重试策略。
- 对 Tavily API 与博查 API 的失败做分级降级处理，避免单点失败导致整个任务不可用。
- 对创建任务接口增加用户级并发限制，避免单个用户持续占满研究队列。
- 对 `.env` 中的 `TAVILY_API_KEY` 与 `BOCHA_API_KEY` 缺失情况做启动期或运行期显式校验。

## 16. 测试策略

第一版建议覆盖以下层次的测试。

### 16.1 单元测试

覆盖内容：

- 状态机流转校验
- 反馈轮数限制
- feedback 计数公式与剩余次数计算
- 任务启动条件校验
- stale task 丢弃逻辑
- 幂等重复执行校验
- 任务详情序列化
- Tavily 与博查结果归一化、去重与降级逻辑
- 并发创建请求下的用户级互斥保护
- `selected_revision` 与 `is_selected` 的事务内一致性

### 16.2 集成测试

覆盖内容：

- 创建任务后是否成功投递分析师任务
- 提交反馈后是否正确生成新 revision
- 启动正式研究后是否锁定 selected revision
- 旧的 analyst 任务延迟执行时是否被正确丢弃
- 旧的 research 任务重复执行时是否不会覆盖新状态
- Tavily 失败但博查成功时是否仍能完成研究流程
- Tavily 与博查都失败时是否进入降级路径而非直接崩溃
- 正式研究完成后是否正确落库报告
- 并发发送两个创建请求时是否最多只成功一个
- 启动研究后是否只有一个 revision 被标记为 `is_selected = true`

### 16.3 API 测试

覆盖内容：

- 鉴权校验
- 只能访问自己的任务
- 非法状态下调用 `feedback/start` 的错误响应
- 超过用户并发限制时创建任务的错误响应
- 未完成任务获取报告时的返回行为

## 17. 演进路线

在第一版稳定后，可继续考虑以下扩展：

- 增加 SSE 进度推送。
- 支持报告导出为 PDF 或富文本。
- 支持报告分享和历史版本比较。
- 为正式研究阶段增加更细的中间产物可视化。
- 如需支持取消，补充 `/tasks/{id}/cancel` 接口和 worker 协作式停止机制。
- 评估是否需要引入 LangGraph 持久化 checkpoint，以支持更多人工干预节点。

## 18. 推荐实施顺序

建议按如下顺序实施：

1. 建立数据模型与 Alembic 迁移。
2. 建立 Schema 和 Service。
3. 增加 DeepResearch API 路由。
4. 抽离原型中的分析师生成逻辑。
5. 接入分析师 Celery 任务。
6. 接入正式研究 Celery 任务。
7. 补齐任务详情和报告查询接口。
8. 补充单元测试、集成测试和 API 测试。

## 19. 结论

DeepResearch 第一版应作为独立业务域实现，而不是并入现有聊天接口。实现上采用“业务状态机 + 双 Celery 任务 + 持久化版本记录”的方案，可以在控制复杂度的前提下，支持分析师草案的有限多轮自然语言反馈，并满足长期保存研究记录的产品目标。

该方案与当前项目现有的 FastAPI、SQLAlchemy 和 Celery 结构高度兼容，能够以较低风险完成第一版后端落地，同时为后续的 SSE 进度推送、更多人工干预节点和报告能力扩展保留清晰的演进空间。
