# Deep Research 报告质量收敛设计文档

> Goal: 参考 [research_assistant.py](D:/Code/python/AILearningCoach/research_assistant.py)，将当前 Deep Research 后端收敛为“分析师并行研究 -> section 并行产出 -> 引言/主体/结论并行撰写 -> 最终报告整合”的高质量报告生成链路。

## 设计结论

当前 worktree 中的 Deep Research 后端已经具备可运行的主图和访谈子图，但最终报告质量仍存在三个核心问题：

1. 主体内容不够厚，容易呈现为“有引言、有结论、中间内容发虚”。
2. section 对最终报告的支撑不够强，内容更像短 memo，而不是面向总报告的高质量研究小节。
3. 引用区过量，URL 缺乏收口策略，影响最终阅读体验。

本轮不重写整套系统，而是在保留现有目录结构、服务层和 API 外壳的前提下，按 [research_assistant.py](D:/Code/python/AILearningCoach/research_assistant.py) 的工作流和 prompt 思路，收敛 graph 行为与输出质量。

## 目标流程

最终目标流程如下：

1. 先生成分析师。
2. 在 `human_feedback` 节点中断，等待用户确认或自然语言反馈重生分析师。
3. 用户确认后，多个分析师各自进入并行子图。
4. 每个子图内部通过并行搜索节点同时检索 `Tavily` 和 `Bocha`。
5. 每个子图最终产出一个属于自己视角的高质量 `section`。
6. 主图收齐所有 section 后，并行生成：
   - `introduction`
   - `content`
   - `conclusion`
7. 最后统一进入 `finalize_report` 生成完整报告。

## 与参考实现的对齐原则

参考行为文件：

- [research_assistant.py](D:/Code/python/AILearningCoach/research_assistant.py)

本轮对齐重点不是逐行复制，而是统一以下设计思想：

1. **Map-Reduce 主流程**
   - analyst 生成后并行开展研究
   - 每个 analyst 负责一个清晰的主题视角
   - 最终由统一整合层汇总报告

2. **子图内部的并行搜索**
   - 问题生成后，两个搜索节点并行执行
   - 搜索结果在回答节点之前完成汇聚

3. **基于 section 的最终报告生成**
   - 最终报告不直接依赖原始访谈文本
   - 而是依赖 analyst section 作为高质量中间产物

4. **引言 / 主体 / 结论并行写作**
   - 在主图收齐全部 section 后并行生成三个部分
   - `finalize_report` 只负责最后整合，而不是承担主要写作职责

## 当前实现存在的问题

### 1. Prompt 过于简化

当前 [prompts.py](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/app/ai/deep_research/prompts.py) 相比 [research_assistant.py](D:/Code/python/AILearningCoach/research_assistant.py) 已经被压缩，导致几个质量问题：

- `section_writer_instructions` 对小节的结构约束太弱
- `report_writer_instructions` 没有明确要求形成厚实的主体内容结构
- `intro_conclusion_instructions` 对引言和结论的角色边界不够清晰

### 2. section 中间产物不够强

当前 [write_section](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/app/ai/deep_research/nodes.py) 虽然会产出 `section_document`，但仍有两个不足：

- section 更像短摘要，而不是“可供总报告编排的专题小节”
- 缺少对“背景 / 核心发现 / 关键事实 / 结论性判断”的稳定约束

### 3. write_report 对主体内容整合不够充分

当前 [write_report](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/app/ai/deep_research/nodes.py) 仍偏向“把 memo 合成一段总结”，没有足够强地要求模型构建完整主体内容，因此容易出现：

- 主体过短
- 只有总述，没有层次
- 与引言、结论相比显得中间薄弱

### 4. 引用收口不足

当前 [finalize_report](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/app/ai/deep_research/nodes.py) 已能输出真实 URL，但仍存在：

- 所有来源都倾向于进入最终引用区
- 缺乏“高价值 URL 限量输出”
- 没有从 section 层面筛选更重要的来源

## 核心设计

### 主图结构

主图维持现有职责边界，但明确为以下流程：

```text
START
  -> create_analysts
  -> human_feedback
  -> dispatch_interviews
  -> conduct_interview x N
  -> write_report
  -> write_introduction
  -> write_conclusion
  -> finalize_report
  -> END
```

关键要求：

- `conduct_interview` 是 analyst 级并行 map 步骤
- `write_report / write_introduction / write_conclusion` 必须在 section 收齐后并行开始
- `finalize_report` 不负责重新生成核心内容，只负责整合与清理

### 子图结构

子图维持现有并行搜索设计，但收紧输出目标：

```text
START
  -> ask_question
  -> dispatch_search
  -> search_web + search_bocha
  -> answer_question
  -> route_messages
  -> ask_question | save_interview
  -> write_section
  -> END
```

关键要求：

- `search_web` 和 `search_bocha` 必须继续并行
- `write_section` 必须成为稳定、可复用的中间产物生成节点

## Prompt 收敛策略

### 1. 分析师生成

目标：

- analyst 不只是“不同职业”
- 而是“不同研究切面”

需要保留 [research_assistant.py](D:/Code/python/AILearningCoach/research_assistant.py) 中这类思想：

- 从主题中找出最值得研究的子主题
- 每个 analyst 对应一个鲜明的关注焦点
- 人类反馈直接改变 analyst 人设分布

### 2. 问题生成

目标：

- analyst 按自己的人设持续深入追问
- 问题应促使专家给出事实、案例、趋势、争议点，而不是泛泛描述

### 3. 回答生成

目标：

- 专家回答只允许使用搜索上下文
- 回答中稳定带编号引用
- 回答内容要足够支持后续 section 写作

### 4. 小节写作

`write_section` 的 prompt 需要恢复到更接近 [research_assistant.py](D:/Code/python/AILearningCoach/research_assistant.py) 的结构化约束。

每个 section 应明确包含：

- `## 小节标题`
- `### 摘要`
- 提炼后的正文
- 来自上下文的关键事实与案例
- 适度的数字引用

同时要明确要求：

- 不是直接复述对话
- 而是把访谈与检索结果提炼成面向最终报告的研究小节
- 小节长度要能支撑后续总报告形成真正的主体内容

### 5. 主体内容写作

`write_report` 是本轮质量提升的核心。

目标：

- 基于所有 section 形成一个厚实的“主体内容”部分
- 不是摘要，而是整篇报告的主干

要求：

- 从多个 section 中抽出 2 到 4 个核心层次
- 合并重复观点
- 建立更清晰的叙述推进
- 保留关键引用
- 只输出主体内容，不输出最终 Sources

最终主体应使用如下结构：

```text
## 主体内容
### 子主题一
...
### 子主题二
...
```

### 6. 引言与结论

`write_introduction` 与 `write_conclusion` 继续并行，但目标更明确：

- `introduction`：预告研究范围、关键张力和主体重点
- `conclusion`：回收主体观点并给出最终判断

两者都应明显短于主体内容，避免喧宾夺主。

## section 中间产物设计

本轮不新增数据库持久化，只强化运行态中间产物。

建议保留并强化以下结构：

- `sections: list[str]`
- `section_documents: list[dict]`

每个 `section_document` 应至少包含：

- `title`
- `content`
- `sources`

后续允许扩展但当前不必强制持久化的字段：

- `focus`
- `key_claims`

## 最终报告结构

最终报告统一输出为：

```text
# 报告标题
## 引言
...

## 主体内容
### 子主题一
...
### 子主题二
...

## 结论
...

## 引用
...
```

说明：

- 标题和正文章节全部使用中文
- `主体内容` 是整个报告的主干
- `引用` 区只展示经过去重和筛选后的高价值来源

## 引用收口策略

最终引用区不再“尽可能全列”，而应“有节制地保留最重要来源”。

策略如下：

1. 仍以 `section_documents.sources` 为唯一事实来源。
2. 先按 URL 去重。
3. 再按 section 顺序保留来源。
4. 每个 section 的最终引用数量设置上限。
5. 全报告最终引用数量设置总上限。

第一版建议策略：

- 每个 section 最多保留 `2-3` 条高价值 URL
- 全报告总引用建议不超过 `8-12` 条

## 非目标

本轮不做以下事项：

- 不重写服务层 API
- 不改变任务状态机
- 不增加中间状态数据库持久化
- 不引入复杂的重试、降级、压测机制
- 不新增第三搜索源

## 影响文件

本轮预计重点修改：

- [prompts.py](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/app/ai/deep_research/prompts.py)
- [nodes.py](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/app/ai/deep_research/nodes.py)
- [graph_builder.py](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/app/ai/deep_research/graph_builder.py)
- [state.py](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/app/ai/deep_research/state.py)
- [test_graph.py](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/tests/ai/deep_research/test_graph.py)
- [test_nodes.py](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/tests/ai/deep_research/test_nodes.py)
- [test_service.py](D:/Code/python/AILearningCoach/.worktrees/feature-deep-research/tests/ai/deep_research/test_service.py)

## 验收标准

本轮完成后，至少满足以下结果：

1. analyst 子图仍保持并行执行。
2. 子图内 Tavily 与 Bocha 仍保持并行搜索。
3. 每个 analyst 都能稳定产出可用 section。
4. 最终报告稳定包含：
   - 引言
   - 明显充实的主体内容
   - 结论
   - 经过收口的引用
5. `Agent + 3 分析师 + 增加大学教授` 这类真实 case 中，主体内容不再显得明显单薄。

## 下一步

1. 基于本设计文档编写实现计划。
2. 先收敛 prompt 和节点职责。
3. 再补测试，验证 section 质量与最终报告结构。
