# Deep Research 后端收敛计划

> **For agentic workers:** 本计划用于在 `feature/deep-research` worktree 中继续完成后端开发。所有依赖安装、验证和测试都在 `aiCoach` 环境中执行。

**Goal:** 让当前 `app/ai/deep_research` 后端实现稳定对齐 `D:\Code\python\AILearningCoach\research_assistant.py` 的核心行为，并形成可持续迭代的任务式后端能力。

**Architecture:** 保留当前项目中的 API / Service / Model 壳层，以 LangGraph research graph 为核心收敛对象；优先修正 graph 行为、检索抽象、feedback 恢复和失败传播，再补关键测试。

**Tech Stack:** FastAPI, SQLAlchemy, LangChain, LangGraph, langchain_openai, Tavily, second-source adapter

---

## 当前基线

- 工作目录：`D:\Code\python\AILearningCoach\.worktrees\feature-deep-research`
- 当前分支：`feature/deep-research`
- 安全锚点：`codex/deep-research-pre-baseline-20260330`
- 测试环境：`D:\miniconda\envs\aiCoach\python.exe`
- 当前验证：`tests/ai/deep_research` 已在 `aiCoach` 中通过，结果为 `25 passed`

---

## 任务 1：建立后端验证基线

**Files:**
- Modify: `tests/ai/deep_research/test_graph.py`
- Modify: `tests/ai/deep_research/test_nodes.py`
- Modify: `tests/ai/deep_research/test_service.py`

- [ ] 补充比“可编译”更有价值的 graph / node / service 测试。
- [ ] 覆盖最少以下行为：
  - `create_analysts` 结构化输出失败时的降级
  - `route_messages` 的轮次上限和结束语判断
  - `finalize_report` 的报告拼装逻辑
  - `run_research_sync` 在空结果和异常时的状态更新
- [ ] 在 `aiCoach` 环境中运行：

```powershell
$env:PYTHONPATH='.'
& 'D:\miniconda\envs\aiCoach\python.exe' -m pytest tests/ai/deep_research -q
```

- [ ] 提交：

```bash
git add tests/ai/deep_research
git commit -m "test(deep_research): 补强后端验证基线"
```

---

## 任务 2：校准 LLM 与检索抽象

**Files:**
- Modify: `app/ai/deep_research/llm.py`
- Modify: `app/ai/deep_research/config.py`
- Modify: `app/ai/deep_research/tools/tavily.py`
- Modify: `app/ai/deep_research/tools/bocha.py`
- Create or Modify: `app/ai/deep_research/tools/__init__.py`

- [ ] 明确当前 LLM 接入策略继续走 OpenAI-compatible 接口。
- [ ] 把第二检索源从“Bocha 固化实现”抽象成“可替换的 secondary source”。
- [ ] 保留当前 Bocha 代码时，也要让节点层不直接依赖其实现细节。
- [ ] 在配置中补齐与超时、结果数量、检索源开关相关的字段。
- [ ] 增加最小单测或桩测试，验证工具初始化和失败路径。
- [ ] 提交：

```bash
git add app/ai/deep_research/config.py app/ai/deep_research/llm.py app/ai/deep_research/tools
git commit -m "refactor(deep_research): 收敛 LLM 与检索抽象"
```

---

## 任务 3：修正 graph 行为以对齐参考实现

**Files:**
- Modify: `app/ai/deep_research/state.py`
- Modify: `app/ai/deep_research/nodes.py`
- Modify: `app/ai/deep_research/graph_builder.py`

- [ ] 对齐 `research_assistant.py` 的关键行为：
  - 分析师生成后的 human feedback 语义
  - 子图消息流
  - Map-Reduce 风格 section 汇总
  - introduction / conclusion / report 并行生成
- [ ] 清理原型期遗留写法：
  - 非结构化消息构造
  - 脆弱的空值兜底
  - 节点吞错后仍继续完成任务
- [ ] 明确哪些错误允许降级，哪些错误必须中止。
- [ ] 视需要增加注释，解释 graph 路由的关键边界。
- [ ] 提交：

```bash
git add app/ai/deep_research/state.py app/ai/deep_research/nodes.py app/ai/deep_research/graph_builder.py
git commit -m "fix(deep_research): 对齐核心 graph 行为"
```

---

## 任务 4：收敛服务层与任务状态机

**Files:**
- Modify: `app/ai/deep_research/service.py`
- Modify: `app/api/v1/endpoints/deep_research.py`
- Modify: `app/models/research_task.py`
- Modify: `app/schemas/deep_research.py`

- [ ] 让任务状态与图执行真实结果一致。
- [ ] 明确以下状态流转：
  - `pending -> running -> completed`
  - `pending/running -> failed`
  - `running -> cancelled`
  - `waiting_feedback` 或等价表达（如本轮需要）
- [ ] 统一 `execute` 与 `feedback` 的职责边界。
- [ ] 保持 SSE 兼容，但不让 SSE 反向污染服务层设计。
- [ ] 视需要补充错误信息字段或中间状态字段。
- [ ] 提交：

```bash
git add app/ai/deep_research/service.py app/api/v1/endpoints/deep_research.py app/models/research_task.py app/schemas/deep_research.py
git commit -m "fix(deep_research): 收敛服务层与任务状态"
```

---

## 任务 5：执行后端集成验证

**Files:**
- Modify: `tests/ai/deep_research/test_api.py`
- Optional: create focused integration helper under `tests/ai/deep_research/`

- [ ] 验证最少以下场景：
  - 创建任务
  - 同步执行任务
  - 异常情况下写入失败状态
  - 提交 feedback 后恢复执行
- [ ] 在 `aiCoach` 环境中执行测试：

```powershell
$env:PYTHONPATH='.'
& 'D:\miniconda\envs\aiCoach\python.exe' -m pytest tests/ai/deep_research -q
```

- [ ] 如果需要，再做一次最小手工调用验证。
- [ ] 提交：

```bash
git add tests/ai/deep_research
git commit -m "test(deep_research): 增加后端集成验证"
```

---

## 任务 6：整理交付状态

**Files:**
- Modify: `docs/deep_research/PROGRESS_2026-03-25.md`
- Optional: add new progress note if needed

- [ ] 更新进度文档，明确：
  - 当前目标已改为对齐 `research_assistant.py`
  - 已废弃或降级的旧设定
  - 当前测试命令以 `aiCoach` 为准
- [ ] 列出剩余风险和下一阶段事项。
- [ ] 提交：

```bash
git add docs/deep_research/PROGRESS_2026-03-25.md
git commit -m "docs(deep_research): 更新后端收敛进度"
```

---

## 执行约束

1. 所有读取统一按 UTF-8。
2. 所有依赖安装与测试均在 `aiCoach` 环境中进行。
3. 不恢复已清理的前端 deep research 草稿。
4. 每个任务结束后优先先跑验证，再提交。
5. 所有提交都留在当前 worktree 分支，保持 `main` 干净。

---

## 第一轮执行建议

按以下顺序开始最稳：

1. 任务 1：补强验证基线
2. 任务 3：修正 graph 行为
3. 任务 4：收敛服务层与状态机
4. 任务 2：回头整理检索抽象
5. 任务 5：执行集成验证
6. 任务 6：更新进度文档
