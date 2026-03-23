# DeepResearch 后端实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在当前项目中落地一个独立于聊天接口的 DeepResearch 后端能力，支持异步任务、有限多轮分析师反馈、正式研究执行和长期保存研究结果。

**架构：** 采用“业务状态机 + 双 Celery 任务 + 持久化版本记录”的方案。API、Service、Celery、AI Runner 和 ORM 模型分层实现，其中分析师草案生成与正式研究执行拆分为两个独立任务，依靠显式 revision 绑定、预期状态校验和 stale task 丢弃来保证幂等和一致性。

**技术栈：** Python、FastAPI、SQLAlchemy、Alembic、Celery、LangGraph、LangChain、DeepSeek、Tavily API、博查 API、PostgreSQL、Redis、Pytest

---

## 文件结构

- 创建：`D:/Code/python/AILearningCoach/app/models/deepresearch.py`
- 修改：`D:/Code/python/AILearningCoach/app/models/__init__.py`
- 创建：`D:/Code/python/AILearningCoach/alembic/versions/<timestamp>_add_deepresearch_tables.py`
- 创建：`D:/Code/python/AILearningCoach/app/schemas/deepresearch.py`
- 创建：`D:/Code/python/AILearningCoach/app/services/deepresearch_service.py`
- 创建：`D:/Code/python/AILearningCoach/app/services/deepresearch_runner.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/deepresearch/__init__.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/deepresearch/models.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/deepresearch/prompts.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/deepresearch/search.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/deepresearch/workflow.py`
- 创建：`D:/Code/python/AILearningCoach/app/tasks/deepresearch_tasks.py`
- 修改：`D:/Code/python/AILearningCoach/app/tasks/__init__.py`
- 修改：`D:/Code/python/AILearningCoach/celery_app.py`
- 创建：`D:/Code/python/AILearningCoach/app/api/v1/endpoints/deepresearch.py`
- 修改：`D:/Code/python/AILearningCoach/app/api/v1/api.py`
- 修改：`D:/Code/python/AILearningCoach/app/core/config.py`
- 修改：`D:/Code/python/AILearningCoach/requirements.txt`
- 创建：`D:/Code/python/AILearningCoach/tests/unit/services/test_deepresearch_service.py`
- 创建：`D:/Code/python/AILearningCoach/tests/unit/tasks/test_deepresearch_tasks.py`
- 创建：`D:/Code/python/AILearningCoach/tests/unit/ai/test_deepresearch_runner.py`
- 创建：`D:/Code/python/AILearningCoach/tests/integration/test_deepresearch_api.py`

## 任务 1：建立 DeepResearch 数据模型与迁移

**文件：**

- 创建：`D:/Code/python/AILearningCoach/app/models/deepresearch.py`
- 修改：`D:/Code/python/AILearningCoach/app/models/__init__.py`
- 创建：`D:/Code/python/AILearningCoach/alembic/versions/<timestamp>_add_deepresearch_tables.py`
- 测试：`D:/Code/python/AILearningCoach/tests/unit/services/test_deepresearch_service.py`

- [ ] **步骤 1：为 ORM 结构和计数字段编写失败测试**

测试应覆盖：

- `DeepResearchTask`
- `DeepResearchAnalystRevision`
- `DeepResearchRun`
- `feedback_round_used == current_revision - 1`
- `selected_revision` 为空与锁定后的两种状态

示例：

```python
def test_feedback_round_used_matches_current_revision():
    task = DeepResearchTask(current_revision=3, feedback_round_used=2)
    assert task.feedback_round_used == task.current_revision - 1
```

- [ ] **步骤 2：运行测试并确认当前失败**

运行：

```bash
pytest tests/unit/services/test_deepresearch_service.py -q
```

预期：

- 因模型不存在或导入失败而报错。

- [ ] **步骤 3：实现 ORM 模型与枚举**

要求：

- 定义 `DeepResearchTaskStatus` 枚举：
  - `pending`
  - `drafting_analysts`
  - `waiting_feedback`
  - `running_research`
  - `completed`
  - `failed`
- 定义 `DeepResearchPhase` 枚举：
  - `analyst_generation`
  - `analyst_feedback`
  - `research_execution`
  - `report_finalization`
- `DeepResearchTask` 保存：
  - `topic`
  - `requirements`
  - `status`
  - `phase`
  - `progress_percent`
  - `progress_message`
  - `current_revision`
  - `feedback_round_used`
  - `max_feedback_rounds`
  - `selected_revision`
  - `final_report_markdown`
  - `final_report_summary`
  - `error_message`
- `DeepResearchAnalystRevision` 保存：
  - `revision_number`
  - `feedback_text`
  - `analysts_json`
  - `is_selected`
- `DeepResearchRun` 保存：
  - `revision_number`
  - `status`
  - `progress_percent`
  - `progress_message`
  - `result_json`
  - `error_message`

- [ ] **步骤 4：编写 Alembic 迁移**

要求：

- 创建 3 张新表及索引
- 为 `task_id + revision_number` 建唯一约束
- 为 `user_id + status` 建查询索引，方便并发限制检查
- 为 `selected_revision` 和 `created_at` 建必要索引

- [ ] **步骤 5：运行模型相关测试**

运行：

```bash
pytest tests/unit/services/test_deepresearch_service.py -q
```

预期：

- 基础 ORM 断言通过。

- [ ] **步骤 6：提交阶段性变更**

```bash
git add app/models/deepresearch.py app/models/__init__.py alembic/versions/<timestamp>_add_deepresearch_tables.py tests/unit/services/test_deepresearch_service.py
git commit -m "feat: add deepresearch persistence models"
```

## 任务 2：实现 Schema 与业务状态机 Service

**文件：**

- 创建：`D:/Code/python/AILearningCoach/app/schemas/deepresearch.py`
- 创建：`D:/Code/python/AILearningCoach/app/services/deepresearch_service.py`
- 测试：`D:/Code/python/AILearningCoach/tests/unit/services/test_deepresearch_service.py`

- [ ] **步骤 1：为 Service 状态流转编写失败测试**

测试应覆盖：

- 创建任务时默认进入 `drafting_analysts`
- 初始 revision 为 `0` 或“待生成下一版”的内部状态时，首次 analyst 任务写回 `revision 1`
- `feedback_round_used` 与 `remaining_feedback_rounds` 的计算
- 超过最大反馈轮数时拒绝反馈
- 存在运行中的任务时拒绝再次创建
- 两个并发创建请求同时进入时最多只成功一个
- `selected_revision` 为权威字段，`is_selected` 仅作冗余展示

示例：

```python
async def test_create_task_rejects_second_running_task(async_session):
    ...
    with pytest.raises(DeepResearchConflictError):
        await service.create_task(...)
```

- [ ] **步骤 2：运行测试并确认失败**

运行：

```bash
pytest tests/unit/services/test_deepresearch_service.py -q
```

预期：

- 因 schema 或 service 缺失而失败。

- [ ] **步骤 3：实现 Pydantic Schema**

至少包含：

- `DeepResearchTaskCreate`
- `DeepResearchFeedbackCreate`
- `DeepResearchTaskSummary`
- `DeepResearchTaskDetail`
- `DeepResearchReportResponse`
- `DeepResearchAnalyst`
- `DeepResearchAnalystRevisionResponse`

要求：

- 对 `topic`、`requirements`、`feedback` 设置长度限制
- 详情响应显式返回：
  - `current_revision`
  - `feedback_round_used`
  - `remaining_feedback_rounds`
  - `analysts`
  - `report_available`

- [ ] **步骤 4：实现 `DeepResearchService`**

核心方法建议包括：

```python
async def create_task(...)
async def list_tasks(...)
async def get_task_detail(...)
async def submit_feedback(...)
async def start_research(...)
async def get_report(...)
async def reserve_next_revision(...)
async def finalize_analyst_revision(...)
async def mark_task_failed(...)
async def create_research_run(...)
async def finalize_research_run(...)
```

要求：

- 在 `create_task` 中检查同用户是否已有 `drafting_analysts/running_research` 任务
- `create_task` 不能只做无锁“先查再写”
- `create_task` 必须在事务中对用户维度做并发保护，至少满足以下之一：
  - 对用户记录执行 `SELECT ... FOR UPDATE`
  - 使用专门的用户级占位锁记录
  - 使用数据库唯一约束 / 锁表实现“同用户最多一个运行中任务”
- 在 `submit_feedback` 中执行轮次校验并为下一版 revision 预留编号
- 在 `start_research` 中以任务表 `selected_revision` 作为唯一权威字段锁定目标 revision
- 所有写状态的方法都提供 compare-and-set 风格的前置条件

- [ ] **步骤 5：为 stale task 防护补充原子更新接口**

实现要求：

- 预留下一版 revision 时使用事务
- analyst 写回前按 `task_id + expected_status + expected_revision` 校验
- 正式研究写回前按 `task_id + selected_revision + expected_status` 校验
- 校验失败时返回“stale/skip”而不是抛出致命异常
- `start_research` 必须在同一事务中：
  - 更新 `deep_research_tasks.selected_revision`
  - 清空该任务其他 revision 的 `is_selected`
  - 将目标 revision 的 `is_selected` 设为 `true`
  - 推进任务状态到 `running_research`
- 不接受只更新任务表或只更新 revision 表的半边实现

- [ ] **步骤 6：运行测试**

运行：

```bash
pytest tests/unit/services/test_deepresearch_service.py -q
```

预期：

- Service 层状态机和计数规则测试通过。

- [ ] **步骤 7：提交阶段性变更**

```bash
git add app/schemas/deepresearch.py app/services/deepresearch_service.py tests/unit/services/test_deepresearch_service.py
git commit -m "feat: add deepresearch service state machine"
```

## 任务 3：搭建 AI Runner 与搜索适配层

**文件：**

- 创建：`D:/Code/python/AILearningCoach/app/ai/deepresearch/__init__.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/deepresearch/models.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/deepresearch/prompts.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/deepresearch/search.py`
- 创建：`D:/Code/python/AILearningCoach/app/ai/deepresearch/workflow.py`
- 创建：`D:/Code/python/AILearningCoach/app/services/deepresearch_runner.py`
- 修改：`D:/Code/python/AILearningCoach/app/core/config.py`
- 修改：`D:/Code/python/AILearningCoach/requirements.txt`
- 测试：`D:/Code/python/AILearningCoach/tests/unit/ai/test_deepresearch_runner.py`

- [ ] **步骤 1：为 runner 接口编写失败测试**

测试应覆盖：

- `generate_analysts()` 返回结构化 analyst 列表
- `run_research()` 返回最终 Markdown 报告和结构化中间结果
- runner 不依赖 `/chat` 会话上下文
- Tavily API 与博查 API 的结果可归一化为统一结构
- 单一搜索供应商失败时可自动降级到另一供应商
- 双供应商都失败时可降级为“仅模型整合 + 局部空来源”

- [ ] **步骤 2：运行测试并确认失败**

运行：

```bash
pytest tests/unit/ai/test_deepresearch_runner.py -q
```

预期：

- 因 runner 或 workflow 模块不存在而失败。

- [ ] **步骤 3：从 demo 抽离纯领域模型与提示词**

迁移来源：

- `research_assistant.py`

迁移要求：

- 将 analyst、perspective、report section 等模型移入 `app/ai/deepresearch/models.py`
- 将中文提示词移入 `prompts.py`
- 不直接在新模块中引用根目录 demo 文件

- [ ] **步骤 4：实现搜索适配层**

要求：

- `search.py` 提供统一接口，例如：
- `.env` 中新增并读取：
  - `TAVILY_API_KEY`
  - `BOCHA_API_KEY`
- `app/core/config.py` 新增对应配置项
- `requirements.txt` 增加 Tavily 对应依赖；博查若使用 HTTP API，则复用现有 `httpx`

```python
class DeepResearchSearchAdapter:
    async def search_web(self, query: str) -> list[dict]: ...
```

- 第一版固定接入 Tavily API 与博查 API，不做通用搜索插件系统
- 固定搜索策略：
  - 默认先查询 Tavily
  - 再查询博查
  - 按 URL 去重并归并结果
  - 保留 `provider` 字段
- 若 Tavily 不可用但博查可用，仍继续流程
- 若博查不可用但 Tavily 可用，仍继续流程
- 若双供应商都不可用，runner 需返回空来源并记录 warning，而不是直接让整个任务崩溃

- [ ] **步骤 5：实现 `DeepResearchRunner`**

要求：

- 提供两个清晰入口：

```python
async def generate_analysts(topic, requirements, max_analysts, feedback_history)
async def run_research(topic, selected_analysts, progress_callback=None)
```

- 封装当前项目可承接的 LLM 调用方式
- 优先复用现有配置体系，而不是把 OpenAI 依赖硬塞进主链路
- 允许通过 `progress_callback` 回传阶段进度，供 Celery 任务落库
- 将搜索实现固定绑定到 Tavily API + 博查 API

- [ ] **步骤 6：运行测试**

运行：

```bash
pytest tests/unit/ai/test_deepresearch_runner.py -q
```

预期：

- Runner 层测试通过。

- [ ] **步骤 7：提交阶段性变更**

```bash
git add app/ai/deepresearch app/services/deepresearch_runner.py app/core/config.py requirements.txt tests/unit/ai/test_deepresearch_runner.py
git commit -m "feat: add deepresearch runner and search adapter"
```

## 任务 4：实现 Celery 任务与幂等防护

**文件：**

- 创建：`D:/Code/python/AILearningCoach/app/tasks/deepresearch_tasks.py`
- 修改：`D:/Code/python/AILearningCoach/app/tasks/__init__.py`
- 修改：`D:/Code/python/AILearningCoach/celery_app.py`
- 测试：`D:/Code/python/AILearningCoach/tests/unit/tasks/test_deepresearch_tasks.py`

- [ ] **步骤 1：为 Celery 任务签名和 stale task 规则编写失败测试**

测试应覆盖：

- `generate_analysts_task(task_id, expected_revision, expected_status)`
- `run_deepresearch_task(task_id, selected_revision, expected_status)`
- 状态不匹配时跳过写回
- revision 不匹配时跳过写回
- 重复执行时不会重复覆盖结果

- [ ] **步骤 2：运行测试并确认失败**

运行：

```bash
pytest tests/unit/tasks/test_deepresearch_tasks.py -q
```

预期：

- 因 Celery 任务模块不存在或函数签名不匹配而失败。

- [ ] **步骤 3：实现 Celery 任务入口**

要求：

- 沿用现有 `run_async()` 封装风格
- analyst 任务从 service 层读取预留 revision
- research 任务从 service 层读取锁定后的 `selected_revision`
- 所有任务在开始前、写回前都重新校验状态

- [ ] **步骤 4：将 DeepResearch 任务注册到 Celery**

要求：

- 在 `celery_app.py` 的 `include` 中增加 `app.tasks.deepresearch_tasks`
- 保持现有异步任务不受影响

- [ ] **步骤 5：实现失败与 stale task 行为**

要求：

- stale task：记录日志并安全退出
- 真正失败：更新主任务和 run 记录为 `failed`
- 对外不抛出会导致无限重试的非预期异常，除非明确希望 Celery 重试

- [ ] **步骤 6：运行测试**

运行：

```bash
pytest tests/unit/tasks/test_deepresearch_tasks.py -q
```

预期：

- 幂等、防重和 stale task 测试通过。

- [ ] **步骤 7：提交阶段性变更**

```bash
git add app/tasks/deepresearch_tasks.py app/tasks/__init__.py celery_app.py tests/unit/tasks/test_deepresearch_tasks.py
git commit -m "feat: add deepresearch celery tasks"
```

## 任务 5：实现 DeepResearch API 接口

**文件：**

- 创建：`D:/Code/python/AILearningCoach/app/api/v1/endpoints/deepresearch.py`
- 修改：`D:/Code/python/AILearningCoach/app/api/v1/api.py`
- 测试：`D:/Code/python/AILearningCoach/tests/integration/test_deepresearch_api.py`

- [ ] **步骤 1：为 API 路由编写失败测试**

测试应覆盖：

- `POST /api/v1/deepresearch/tasks`
- `GET /api/v1/deepresearch/tasks`
- `GET /api/v1/deepresearch/tasks/{id}`
- `POST /api/v1/deepresearch/tasks/{id}/feedback`
- `POST /api/v1/deepresearch/tasks/{id}/start`
- `GET /api/v1/deepresearch/tasks/{id}/report`

- [ ] **步骤 2：运行测试并确认失败**

运行：

```bash
pytest tests/integration/test_deepresearch_api.py -q
```

预期：

- 因路由不存在返回 404 或导入失败。

- [ ] **步骤 3：实现 API 路由**

要求：

- 对齐现有 endpoint 风格，使用 `Depends(get_current_active_user)` 和 `Depends(get_db)`
- 创建任务时返回任务摘要，不阻塞等待 analyst 生成
- `feedback` 接口只接受自然语言反馈，不暴露 analyst CRUD
- `start` 接口只负责锁定 revision 并投递研究任务

- [ ] **步骤 4：接入统一错误处理**

要求：

- 轮次超限返回 409 或 400 的业务错误
- 并发限制返回明确业务错误
- 非本人任务返回 404 或 403，遵循现有项目风格

- [ ] **步骤 5：注册路由**

修改：

- `app/api/v1/api.py`

要求：

- 增加 `deepresearch` router
- 不影响现有路由前缀和 tags

- [ ] **步骤 6：运行测试**

运行：

```bash
pytest tests/integration/test_deepresearch_api.py -q
```

预期：

- DeepResearch 接口测试通过。

- [ ] **步骤 7：提交阶段性变更**

```bash
git add app/api/v1/endpoints/deepresearch.py app/api/v1/api.py tests/integration/test_deepresearch_api.py
git commit -m "feat: add deepresearch api endpoints"
```

## 任务 6：补充端到端状态与报告集成测试

**文件：**

- 修改：`D:/Code/python/AILearningCoach/tests/unit/services/test_deepresearch_service.py`
- 修改：`D:/Code/python/AILearningCoach/tests/unit/tasks/test_deepresearch_tasks.py`
- 修改：`D:/Code/python/AILearningCoach/tests/unit/ai/test_deepresearch_runner.py`
- 修改：`D:/Code/python/AILearningCoach/tests/integration/test_deepresearch_api.py`

- [ ] **步骤 1：补充完整主流程测试**

覆盖链路：

1. 创建任务
2. 生成初始 analyst revision 1
3. 提交一次 feedback 并生成 revision 2
4. 确认 revision 2 并启动研究
5. 正式研究完成并保存报告
6. 校验任务表 `selected_revision` 与 revision 表 `is_selected` 一致

- [ ] **步骤 2：补充异常分支测试**

覆盖内容：

- 旧 analyst 任务延迟写回被丢弃
- 旧 research 任务重复执行被丢弃
- 超过 3 轮 feedback 被拒绝
- 进行中任务并发创建被拒绝
- 两个并发创建请求同时进入时不会产生两条运行中任务
- 未完成时获取报告返回明确状态

- [ ] **步骤 3：运行核心测试集**

运行：

```bash
pytest tests/unit/services/test_deepresearch_service.py tests/unit/tasks/test_deepresearch_tasks.py tests/unit/ai/test_deepresearch_runner.py tests/integration/test_deepresearch_api.py -q
```

预期：

- 核心功能测试全部通过。

- [ ] **步骤 4：进行 Alembic 冒烟验证**

运行：

```bash
alembic upgrade head
```

预期：

- DeepResearch 新表迁移成功。

- [ ] **步骤 5：提交阶段性变更**

```bash
git add tests/unit/services/test_deepresearch_service.py tests/unit/tasks/test_deepresearch_tasks.py tests/unit/ai/test_deepresearch_runner.py tests/integration/test_deepresearch_api.py
git commit -m "test: cover deepresearch end-to-end workflow"
```

## 任务 7：联调、文档对齐与最终验证

**文件：**

- 修改：`D:/Code/python/AILearningCoach/docs/superpowers/specs/2026-03-23-deepresearch-design.md`（仅在实现偏差时）
- 修改：`D:/Code/python/AILearningCoach/docs/superpowers/plans/2026-03-23-deepresearch-backend-implementation.md`（勾选完成项时）

- [ ] **步骤 1：执行完整测试回归**

运行：

```bash
pytest tests/unit/services/test_deepresearch_service.py tests/unit/tasks/test_deepresearch_tasks.py tests/unit/ai/test_deepresearch_runner.py tests/integration/test_deepresearch_api.py -q
```

预期：

- DeepResearch 相关测试全部通过。

- [ ] **步骤 2：执行 API 冒烟联调**

建议顺序：

1. 调用创建任务接口
2. 模拟 analyst Celery 任务执行
3. 调用详情接口确认 revision 和剩余轮次
4. 调用 feedback 接口
5. 调用 start 接口
6. 模拟 research Celery 任务执行
7. 调用 report 接口确认最终报告返回

- [ ] **步骤 3：核对实现与 spec 是否一致**

检查清单：

- 是否仍为独立于 `/chat` 的业务域
- 是否只有有限多轮自然语言反馈
- 是否移除了第一版 `cancelled` 可达状态
- 是否实现用户级并发限制
- 是否实现 Celery 显式 revision 绑定和 stale task 丢弃
- 是否将报告长期保存在任务主记录中

- [ ] **步骤 4：记录偏差并回写 spec（如有）**

仅当实现和设计不一致时更新：

- `docs/superpowers/specs/2026-03-23-deepresearch-design.md`

- [ ] **步骤 5：提交最终集成变更**

```bash
git add .
git commit -m "feat: ship deepresearch backend workflow"
```

## 风险与注意事项

- 当前仓库主 AI 配置是 DeepSeek，而 demo 使用的是 OpenAI 风格接口；实现时必须先统一 provider 边界，不能直接把 demo 依赖塞进主链路。
- 搜索层已明确固定为 Tavily API + 博查 API；实现时不要重新抽象成无限供应商插件系统，避免第一版过度设计。
- `research_assistant.py` 当前是根目录 demo 文件，应作为迁移参考而不是运行时依赖；新实现应完全落在 `app/ai/deepresearch/` 与 `app/services/` 下。
- Celery 重复投递、手工重试和 worker 重启后的重复消费必须按常态处理，任何只传 `task_id` 的实现都不满足本计划要求。
- 用户级并发限制不能只靠应用层“先查再拒绝”，必须加事务级或数据库级互斥保护。
- `deep_research_tasks.selected_revision` 是唯一权威字段；`is_selected` 仅用于冗余展示，更新时必须事务内同步。
- `feedback_round_used`、`current_revision`、`remaining_feedback_rounds` 的公式必须在 schema、service、API 返回值和测试中保持完全一致。
- 必须显式处理 `.env` 中 `TAVILY_API_KEY`、`BOCHA_API_KEY` 缺失，以及单供应商失败和双供应商同时失败三类场景。
- 当前会话存在用户已有未提交变更；执行计划时不要覆盖与 DeepResearch 无关的工作区内容。
