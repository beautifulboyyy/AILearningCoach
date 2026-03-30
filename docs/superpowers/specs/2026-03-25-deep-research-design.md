# Deep Research 功能设计文档

> **Goal:** 在现有 AILearningCoach 项目中实现一个可持续迭代的 Deep Research 后端，其核心行为参考 `D:\Code\python\AILearningCoach\research_assistant.py`，并通过项目现有的 FastAPI / SQLAlchemy / LangGraph 架构对外提供能力。

## 设计结论

当前 worktree 中的 `app/ai/deep_research` 已经具备一套可运行的后端雏形，且在 `aiCoach` 环境下通过了现有测试基线。后续开发不再重新造一套新系统，而是采用以下策略：

1. 保留当前项目中的目录布局、数据库模型、服务层和 API 壳子。
2. 以 `research_assistant.py` 的工作流行为作为最终目标参考。
3. 优先对齐核心 research graph 的行为，而不是继续扩展前端或 SSE 外壳。

## 目标行为

最终的 Deep Research 后端需要具备以下能力：

- 根据研究主题生成多位分析师。
- 在分析师生成后支持单点 human feedback。
- 为每位分析师并行启动访谈子图。
- 每轮访谈支持“问题生成 -> 多源检索 -> 专家回答 -> 路由判断”。
- 将各分析师产出的 section 汇总为 introduction / content / conclusion / final_report。
- 保留任务状态、最终报告和必要的中间信息。

## 对齐参考实现

行为参考文件：

- `D:\Code\python\AILearningCoach\research_assistant.py`

重点对齐内容：

1. **Graph 结构**
   - 主图为 `create_analysts -> human_feedback -> conduct_interview -> write_* -> finalize_report`
   - 子图为 `ask_question -> search -> answer_question -> route -> save_interview -> write_section`

2. **Human-in-the-loop**
   - `human_feedback` 是图中的正式中断点，不是单纯的 API 附属逻辑。
   - 后端需要支持“生成分析师后暂停，收到反馈后继续或重生成人设”。

3. **检索抽象**
   - 参考实现使用 `Tavily + 百科知识源`。
   - 当前项目中的第二搜索源应改造成“百科/知识源适配器优先”，而不是把 Bocha 绑定成唯一方案。

4. **结构化输出**
   - 分析师生成和搜索查询生成都应使用结构化输出。
   - 不再回退到脆弱的手写 JSON 解析流程。

## 技术选型

- **框架**: LangChain + LangGraph
- **LLM**: OpenAI-compatible Chat API via `langchain_openai`
- **检索主源**: Tavily
- **检索副源**: 百科/知识源适配器（第一版可兼容当前 Bocha 封装，但目标接口按参考实现抽象）
- **持久化**: PostgreSQL 中的 `research_tasks`
- **服务层**: FastAPI + SQLAlchemy AsyncSession
- **图状态**: LangGraph + MemorySaver（当前阶段）

## 非目标

当前阶段不做以下事项：

- 不继续投入前端 deep research 页面开发。
- 不把 SSE 当作核心架构前提。
- 不与远端 `deepresearch` 简化版实现做代码级融合。
- 不在本轮引入复杂队列化执行或 Celery 异步任务编排。

## 当前落地目录

```text
app/ai/deep_research/
├── config.py
├── graph_builder.py
├── llm.py
├── nodes.py
├── prompts.py
├── service.py
├── state.py
└── tools/
    ├── bocha.py
    └── tavily.py

app/api/v1/endpoints/deep_research.py
app/models/research_task.py
app/schemas/deep_research.py
tests/ai/deep_research/
```

## 核心架构

### 主图

```text
START
  -> create_analysts
  -> human_feedback
  -> [Send] conduct_interview x N
  -> write_report
  -> write_introduction
  -> write_conclusion
  -> finalize_report
  -> END
```

### 访谈子图

```text
START
  -> ask_question
  -> search_primary
  -> search_secondary
  -> answer_question
  -> route_messages
  -> ask_question | save_interview
  -> write_section
  -> END
```

## 状态模型

### GenerateAnalystsState

- `topic: str`
- `max_analysts: int`
- `human_analyst_feedback: str | None`
- `analysts: list`

### InterviewState

- `messages`
- `max_num_turns`
- `context`
- `analyst`
- `interview`
- `sections`

### ResearchGraphState

- `topic`
- `max_analysts`
- `human_analyst_feedback`
- `analysts`
- `sections`
- `introduction`
- `content`
- `conclusion`
- `final_report`

## API 设计原则

当前 API 以“任务式后端”提供能力，而不是直接暴露参考实现中的脚本交互模式。

保留的后端职责：

- 创建任务
- 查询任务
- 执行任务
- 提交 human feedback
- 取消任务

接口传输形式说明：

- `execute` 作为当前推荐执行入口。
- `events` / SSE 仅作为兼容能力，不再作为设计中心。
- 若后续 human feedback 恢复为真正中断执行，需要让服务层显式暴露“等待反馈”状态。

## 错误处理策略

后续实现必须满足以下规则：

1. **LLM 或检索失败不能静默伪成功**
   - 节点失败时应区分“可降级继续”和“必须终止任务”。

2. **任务状态必须与图执行结果一致**
   - `completed` 只允许在最终报告有效时写入。
   - `failed` 应记录错误摘要。

3. **外部调用需要超时和重试边界**
   - LLM、Tavily、第二检索源都需要有限重试和超时。

4. **human feedback 状态要可恢复**
   - 不能出现 graph 暂停后无法继续的死状态。

## 测试策略

后续测试分三层：

1. **单元测试**
   - 节点函数的结构化输出、路由、报告整合。

2. **服务层测试**
   - 任务创建、状态迁移、失败传播、反馈恢复。

3. **集成验证**
   - 在 `aiCoach` 环境中跑通最小 happy path。

当前已有测试只足以证明“代码可导入、局部函数可运行”，不足以覆盖最终需求。

## 版本管理约束

- 所有开发只在 `D:\Code\python\AILearningCoach\.worktrees\feature-deep-research` 中进行。
- `main` 保持为远端干净基线。
- 当前 worktree 的安全锚点分支为 `codex/deep-research-pre-baseline-20260330`。
- 后续按“小步提交、单主题 commit”的方式推进后端修复。

## 当前状态

- worktree 分支：`feature/deep-research`
- 基线提交：`f385d99`
- `aiCoach` 环境测试结果：`25 passed`
- 前端 WIP：已清理

## 下一步

1. 修订实现计划，使其围绕“后端收敛”和“参考实现对齐”展开。
2. 做第一轮后端验证：
   - graph 同步执行
   - feedback 中断/恢复
   - 搜索抽象现状
   - 失败传播
3. 基于验证结果进入实现。
