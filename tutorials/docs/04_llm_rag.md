# 大模型与 RAG 学习

## 这套项目的 AI 架构
1. Orchestrator 先做意图识别。
2. 选择对应 Agent（QA/Planner/Analyst/Coach）。
3. Agent 内部可能调用 RAG 或直接 LLM。
4. 结果以流式 chunk 返回前端。

关键文件：
- [app/ai/agents/orchestrator.py](/D:/Code/python/AILearningCoach/app/ai/agents/orchestrator.py)
- [app/ai/rag/retriever.py](/D:/Code/python/AILearningCoach/app/ai/rag/retriever.py)
- [app/ai/rag/generator.py](/D:/Code/python/AILearningCoach/app/ai/rag/generator.py)
- [app/ai/rag/llm.py](/D:/Code/python/AILearningCoach/app/ai/rag/llm.py)

## 你要讲清楚的 4 个概念
1. Multi-Agent：按任务类型拆职责，提高回复稳定性和可扩展性。
2. RAG：先检索再生成，减少“无依据胡说”。
3. Hybrid Retrieval：向量检索 + 关键词检索 + rerank，提升召回质量。
4. Stream Generation：边生成边返回，提升体感速度。

## 代码里真实做法（可面试引用）
- 意图识别优先规则匹配，置信度不足再走 LLM 识别。
- `retriever.hybrid_retrieve` 融合向量分数与 BM25 分数。
- `generator.generate_stream` 先发 metadata，再发 answer chunk。
- LLM 客户端封装了重试逻辑（tenacity）。

## 你可以做的 AI 方向改进（高价值）
1. 给意图识别加离线评估集和准确率报告。
2. 给检索加命中率统计（top-k 命中、来源分布）。
3. 对低置信度回答增加“免责声明 + 追问建议”。

## 面试问答速记
- Q: 为什么不用一个大 prompt 解决全部？
- A: 多任务场景下可维护性和稳定性差；分 Agent 可以做职责隔离、独立优化和监控。

- Q: 为什么要 RAG？
- A: 让答案尽量基于知识库证据，降低幻觉，且可追溯来源。
