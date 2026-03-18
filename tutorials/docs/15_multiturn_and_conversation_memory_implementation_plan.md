# 多轮对话与 Conversation 级记忆实施方案

这份方案基于当前项目现状和当前学习目标进行收敛。

本次改造**不引入用户级长期记忆**，也**不修改现有用户画像系统**。  
本次只聚焦三个目标：

1. 实现真正的多轮对话
2. 引入基于 Redis 的短期工作记忆
3. 为 `Conversation` 增加可持久化的会话级摘要

## 一、改造目标

当前项目已经具备：

1. `Conversation` / `Message` 的原始消息落库
2. Redis 封装
3. 记忆管理器中的短期记忆能力
4. Celery 异步任务体系

但当前主聊天链路仍存在两个关键缺口：

1. 历史消息虽然存下来了，但没有真正重新注入模型
2. conversation 级上下文没有形成“热记忆 + 持久摘要”双层结构

本次改造完成后，希望达到：

1. 用户连续追问时，模型能记住最近几轮原文上下文
2. 长 conversation 中，窗口外的重要信息可以由 Redis 热记忆补足
3. 用户隔较长时间回到同一 conversation 时，系统仍能恢复会话主线

## 二、最终分层设计

本次只保留三层：

### 1. 最近消息窗口

来源：

`messages` 表

作用：

1. 保留最近 `N` 条原始对话
2. 实现真正的多轮连续性

使用方式：

直接作为结构化 `messages` 历史传给模型，而不是拼成一段普通文本。

### 2. Redis 短期工作记忆

来源：

Redis

作用：

1. 作为活跃 conversation 的热记忆层
2. 记录窗口之外但仍属于当前 conversation 的近期重点
3. 减少每次都回扫大量历史 message 的成本

特点：

1. 读写快
2. 可设置 TTL
3. 面向当前活跃会话

### 3. Conversation 持久摘要

来源：

PostgreSQL `Conversation`

作用：

1. 持久化保存当前 conversation 的阶段性总结
2. 在 Redis 过期后仍能恢复 conversation 主线
3. 为长时间后的会话恢复提供基础

## 三、明确不做的部分

为了让本次改造目标聚焦，以下内容暂时不纳入本轮：

1. 用户级长期记忆
2. Memory + Milvus 的用户记忆检索回注
3. 用户画像结构调整
4. 跨 conversation 的长期个性化记忆

这些内容后续可以作为下一轮迭代。

## 四、改造主线

本次改造建议按三条主线推进：

1. 多轮对话主线
2. Redis 短期记忆主线
3. Conversation 摘要持久化主线

## 五、多轮对话实施方案

### 目标

让模型在每次聊天请求中真正看到最近几轮原始对话。

### 现状问题

当前 [chat.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/chat.py) 虽然会保存 `Message`，但并没有把历史消息重新喂给模型。

### 改造步骤

#### 1. 在 `chat` 和 `chat_stream` 中提取最近消息窗口

在确定当前 `conversation` 后，调用 agent 之前：

1. 查询当前 `conversation_id` 下最近 `N` 条消息
2. 建议按时间顺序整理
3. 建议先取最近 `4-6` 条，作为第一版窗口

#### 2. 将最近消息转换为标准 `messages` 格式

建议格式：

```python
[
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
]
```

这部分应作为：

真实对话历史

而不是普通背景文本。

#### 3. 修改 Agent / RAG / LLM 调用方式

当前很多地方是：

```python
messages=[{"role": "user", "content": huge_prompt}]
```

本次改造后建议改成：

```python
messages = [
    {"role": "system", "content": system_prompt},
    *recent_history,
    {"role": "user", "content": current_user_input},
]
```

### 需要修改的重点文件

1. [chat.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/chat.py)
2. [qa_agent.py](/D:/Code/python/AILearningCoach/app/ai/agents/qa_agent.py)
3. [planner_agent.py](/D:/Code/python/AILearningCoach/app/ai/agents/planner_agent.py)
4. `coach_agent.py`
5. `analyst_agent.py`
6. [generator.py](/D:/Code/python/AILearningCoach/app/ai/rag/generator.py)
7. [llm.py](/D:/Code/python/AILearningCoach/app/ai/rag/llm.py)

### 预期效果

完成后：

1. 最近几轮上下文真正参与模型推理
2. 当前系统从“保存历史但不使用”升级到“基础多轮对话”

## 六、Redis 短期记忆实施方案

### 目标

在最近消息窗口之外，再增加一层会话级热记忆，用于补足较长 conversation 的近期上下文。

### 现有基础

项目已经有：

1. [cache.py](/D:/Code/python/AILearningCoach/app/utils/cache.py)
2. [manager.py](/D:/Code/python/AILearningCoach/app/ai/memory/manager.py) 中的：
   - `save_short_term_memory`
   - `get_short_term_memory`

### 设计原则

Redis 短期记忆不负责永久保存整个 conversation，而负责：

1. 保存活跃 conversation 的热状态
2. 保存窗口外近期重要上下文
3. 为当前活跃会话提供快速补充信息

### 建议存储内容

每轮对话结束后，向 Redis 写入一条结构化记录，例如：

```json
{
  "user_message": "...",
  "assistant_message": "...",
  "intent": "...",
  "agent": "...",
  "timestamp": "..."
}
```

后续可以演进为：

1. 最近主题
2. 关键结论
3. 当前任务状态
4. 最近困难点

### 写入时机

在 [chat.py](/D:/Code/python/AILearningCoach/app/api/v1/endpoints/chat.py) 和 `chat_stream` 中，AI 回复成功落库之后：

1. 写 Redis 短期记忆
2. 不阻塞主响应为优先

### 读取时机

在下一轮进入 `chat` / `chat_stream` 时：

1. 先加载最近消息窗口
2. 再读取 Redis 短期记忆
3. 只取最近几条或压缩后的摘要作为补充上下文

### 使用策略

建议采用：

1. **近处用原文窗口**
2. **窗口外用 Redis 热记忆补充**

不要把 Redis 全量内容直接塞进 prompt。

### TTL 建议

Redis 热记忆建议保留较长但有限的时间，例如：

1. 2 小时
2. 6 小时
3. 24 小时

第一版可以沿用当前 `manager.py` 中已有 TTL 设计，再根据使用体验调整。

## 七、Conversation 持久摘要实施方案

### 目标

解决 Redis 过期后 conversation 主线丢失的问题。

### 设计原则

Redis 负责：

活跃会话的热记忆

PostgreSQL `Conversation` 负责：

当前 conversation 的持久摘要

### 需要修改的数据模型

给 [conversation.py](/D:/Code/python/AILearningCoach/app/models/conversation.py) 中的 `Conversation` 增加字段：

1. `summary`
2. `summary_updated_at`
3. 可选：`topic`

然后新增 Alembic migration。

### 摘要内容建议

conversation summary 应重点保留：

1. 当前会话主要主题
2. 已讨论的关键结论
3. 当前阶段正在解决的问题
4. 对后续继续聊天仍有价值的信息

它不需要保留所有细节。

### 更新时机

建议异步更新，而不是同步更新。

### 建议新增 Celery 任务

例如：

`update_conversation_summary`

任务职责：

1. 读取当前 conversation 最近若干消息
2. 调用 [compressor.py](/D:/Code/python/AILearningCoach/app/ai/memory/compressor.py) 做摘要压缩
3. 更新 Redis 热摘要
4. 更新 PostgreSQL `Conversation.summary`

### 触发策略

建议不要每条消息都重算摘要。

可以考虑以下触发条件：

1. `message_count` 达到某个阈值
2. 每增加若干轮对话更新一次
3. 或在会话结束时额外更新一次

第一版建议简单一些：

每增加 `4-6` 条消息更新一次摘要。

## 八、上下文组装原则

本次改造后，context 建议包含：

```python
context = {
    "user_id": current_user.id,
    "session_id": session_id,
    "user_profile": user_profile,
    "learning_progress": progress_stats,
    "recent_history": recent_history,
    "short_term_memory": short_term_memory,
    "conversation_summary": conversation_summary,
}
```

### 使用规则

#### 进入 `messages` 的

1. `recent_history`
2. 当前用户消息

#### 进入 system/context prompt 的

1. `user_profile`
2. `learning_progress`
3. `short_term_memory`
4. `conversation_summary`

这样可以保持：

1. 真实对话历史和背景信息分层
2. 模型输入结构更清晰

## 九、分阶段实施顺序

建议分三步推进：

### 第一步：补多轮对话

目标：

先让最近几轮原始消息真正参与模型推理。

完成标志：

1. 用户追问上一轮内容时，模型能正确衔接

### 第二步：补 Redis 短期记忆

目标：

让当前 conversation 的窗口外近期重点可以被补回来。

完成标志：

1. conversation 较长时，模型不只依赖最近几轮原文

### 第三步：补 PostgreSQL conversation summary

目标：

让 conversation 在长时间后仍能恢复主线。

完成标志：

1. Redis 过期后仍可依赖 `Conversation.summary`

## 十、验证方案

### 多轮对话验证

测试方式：

1. 连续问 3-5 轮相互依赖的问题
2. 观察模型是否能记住上一轮内容

### Redis 短期记忆验证

测试方式：

1. 人为制造长 conversation
2. 确认窗口外信息可以通过 Redis 热记忆补回来
3. 检查 Redis key 是否正确写入

### Conversation 持久摘要验证

测试方式：

1. 完成长对话
2. 检查数据库中 `Conversation.summary` 是否更新
3. 模拟 Redis 不可用或过期后重新进入 conversation
4. 观察模型是否还能恢复主题

## 十一、实施后的收益

完成本轮改造后，项目会从：

1. 保存消息但不具备真正多轮上下文能力

升级为：

1. 具备最近几轮原文上下文的多轮对话能力
2. 具备 Redis 热工作记忆
3. 具备 PostgreSQL conversation 级持久摘要

这将使聊天系统更接近真实的 AI 助教产品，而不只是带画像的单轮问答系统。

## 十二、一句话总结

本次实施方案的核心思路是：

先用最近消息窗口补齐真正的多轮对话，再用 Redis 维护 conversation 级短期热记忆，最后把 conversation 摘要异步持久化到 PostgreSQL，从而形成“原文窗口 + 热记忆 + 持久摘要”的三层会话级上下文系统。
