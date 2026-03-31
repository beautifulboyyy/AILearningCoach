# Deep Research 报告质量收敛实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 让 Deep Research 后端稳定产出“分析师 section 并行汇总 -> 引言/主体/结论并行撰写 -> 最终高质量报告”的完整链路，并显著提升主体内容密度与引用收口效果。

**架构：** 保留当前 LangGraph 主图与访谈子图骨架，不重写服务层与 API，只收敛 prompt、节点职责和最终报告整合逻辑。先通过测试明确 section 结构、主体内容格式和引用限量行为，再以最小实现改造 `prompts.py`、`nodes.py` 和必要的图汇总节点。

**技术栈：** Python、LangChain、LangGraph、Pydantic、Pytest

---

## 文件结构

### 修改

- `app/ai/deep_research/prompts.py`
  - 参考 `research_assistant.py` 收敛 analyst、section、report、intro/conclusion prompt
- `app/ai/deep_research/nodes.py`
  - 收敛 section 写作、主体内容生成、最终报告整合与引用筛选
- `app/ai/deep_research/graph_builder.py`
  - 确认主图并行边与收敛后的报告节点职责一致
- `tests/ai/deep_research/test_nodes.py`
  - 增补 section、主体、引用收口相关测试
- `tests/ai/deep_research/test_graph.py`
  - 补主图并行写作链路的行为测试

### 参考

- `research_assistant.py`
- `docs/superpowers/specs/2026-03-31-deep-research-report-quality-design.md`

## 任务 1：补 section 与最终报告结构测试

**文件：**
- 修改：`tests/ai/deep_research/test_nodes.py`
- 验证：`pytest tests/ai/deep_research/test_nodes.py -q`

- [ ] **步骤 1：编写失败测试，锁定 section 和最终报告结构**
  - 增加对 `write_section` 的结构测试：要求产出 `## 标题` 且保留 `section_documents`
  - 增加对 `finalize_report` 的结构测试：要求最终报告包含 `## 引言`、`## 主体内容`、`## 结论`、`## 引用`
  - 增加对引用收口的测试：每个 section 限量、全局去重、总量不失控

- [ ] **步骤 2：运行测试验证失败**
  - 运行：`$env:PYTHONPATH='.'; & 'D:\miniconda\envs\aiCoach\python.exe' -m pytest tests/ai/deep_research/test_nodes.py -q`
  - 预期：新增测试失败，暴露当前报告结构与引用限量行为缺口

- [ ] **步骤 3：实现最少代码使测试通过**
  - 在 `nodes.py` 中补 section 和 final report 结构收口逻辑

- [ ] **步骤 4：重跑测试验证通过**
  - 运行同一命令，预期通过

- [ ] **步骤 5：Commit**
  - `git commit -m "test(deep_research): 锁定报告结构与引用收口行为"`

## 任务 2：收敛 prompt 与主体内容生成

**文件：**
- 修改：`app/ai/deep_research/prompts.py`
- 修改：`app/ai/deep_research/nodes.py`
- 验证：`pytest tests/ai/deep_research/test_nodes.py -q`

- [ ] **步骤 1：先补失败测试，锁定主体内容要求**
  - 为 `write_report` 增加测试：要求输出 `## 主体内容`
  - 要求主体内部至少允许多级标题或更有层次的正文骨架
  - 对 `write_introduction`、`write_conclusion` 增加标题约束测试

- [ ] **步骤 2：运行测试验证失败**
  - 运行：`$env:PYTHONPATH='.'; & 'D:\miniconda\envs\aiCoach\python.exe' -m pytest tests/ai/deep_research/test_nodes.py -q`

- [ ] **步骤 3：按参考文件收敛 prompt**
  - 强化 `section_writer_instructions`
  - 强化 `report_writer_instructions`
  - 强化 `intro_conclusion_instructions`
  - 修改 `write_report` 让主体内容成为真正主干而非短总结

- [ ] **步骤 4：重跑测试验证通过**
  - 同上命令，预期通过

- [ ] **步骤 5：Commit**
  - `git commit -m "feat(deep_research): 提升 section 与主体写作质量"`

## 任务 3：收敛主图并行写作链路

**文件：**
- 修改：`app/ai/deep_research/graph_builder.py`
- 修改：`tests/ai/deep_research/test_graph.py`
- 验证：`pytest tests/ai/deep_research/test_graph.py -q`

- [ ] **步骤 1：编写失败测试**
  - 验证主图在 interview 完成后并行触发 `write_report / write_introduction / write_conclusion`
  - 验证最终汇总节点只做整合而不重新承担主体生成职责

- [ ] **步骤 2：运行测试验证失败**
  - 运行：`$env:PYTHONPATH='.'; & 'D:\miniconda\envs\aiCoach\python.exe' -m pytest tests/ai/deep_research/test_graph.py -q`

- [ ] **步骤 3：实现最少必要改动**
  - 如有必要，调整 `graph_builder.py` 边和中间状态保留逻辑

- [ ] **步骤 4：重跑测试验证通过**
  - 同上命令，预期通过

- [ ] **步骤 5：Commit**
  - `git commit -m "refactor(deep_research): 收敛并行报告写作链路"`

## 任务 4：真实链路回归与报告质量验收

**文件：**
- 修改：`app/ai/deep_research/nodes.py`
- 验证：`pytest tests/ai/deep_research -q`

- [ ] **步骤 1：运行完整后端测试**
  - 运行：`$env:PYTHONPATH='.'; & 'D:\miniconda\envs\aiCoach\python.exe' -m pytest tests/ai/deep_research -q`
  - 预期：所有测试通过

- [ ] **步骤 2：必要时补最后的收口修复**
  - 仅处理因新报告结构带来的回归问题

- [ ] **步骤 3：重跑完整后端测试**
  - 同上命令，预期通过

- [ ] **步骤 4：做一次真实 case 回归**
  - 主题：`Agent`
  - 分析师：`3`
  - 反馈：`增加一位大学教授`
  - 验收重点：
    - 引言完整
    - 主体内容明显充实
    - 结论完整
    - 引用收口不过量

- [ ] **步骤 5：Commit**
  - `git commit -m "fix(deep_research): 收口报告质量与最终输出"`
