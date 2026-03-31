# Deep Research API 接口说明

## 概述

Deep Research 当前只保留任务制接口。

后端职责如下：

- 管理任务的创建、查询、删除
- 管理分析师生成与人工确认流程
- 生成并保存最终 `final_report`
- 提供运行时进度查询接口（仅内存态，不长期持久化）

基础前缀：

```text
/api/v1/deep-research
```

## 任务状态

- `pending`：任务已创建，尚未生成分析师
- `awaiting_feedback`：分析师已生成，等待用户确认或重生
- `running`：研究执行中
- `completed`：研究已完成，可读取最终报告
- `failed`：研究执行失败

## 运行时进度阶段

`GET /tasks/{thread_id}/progress` 可能返回以下 `stage`：

- `idle`
- `creating_analysts`
- `awaiting_feedback`
- `running`
- `searching`
- `interviewing`
- `writing_sections`
- `writing_report`
- `finalizing_report`

## 正式接口

### 1. 创建任务

`POST /tasks`

请求体示例：

```json
{
  "topic": "Agent",
  "max_analysts": 3,
  "analyst_directions": ["增加大学教授视角"]
}
```

说明：

- 只创建任务，不会自动开始研究
- 返回 `thread_id`，后续所有任务操作都基于该字段

### 2. 查询任务列表

`GET /tasks?limit=50`

说明：

- 返回任务列表
- 每条任务记录包含基础信息、状态、分析师快照和最终报告字段

### 3. 查询任务详情

`GET /tasks/{thread_id}`

说明：

- 返回单个任务详情
- 若任务处于 `awaiting_feedback`，会返回当前分析师列表
- 若任务处于 `completed`，可从 `final_report` 获取最终报告

### 4. 查询运行时进度

`GET /tasks/{thread_id}/progress`

返回示例：

```json
{
  "thread_id": "research_xxx",
  "stage": "searching",
  "message": "正在并行检索 Tavily 和 Bocha",
  "updated_at": "2026-03-31T15:00:00"
}
```

说明：

- 这是运行时内存数据，不做长期持久化
- 服务重启后，运行中任务的进度不会恢复

### 5. 生成分析师

`POST /tasks/{thread_id}/analysts`

说明：

- 触发分析师生成
- 成功后任务状态会进入 `awaiting_feedback`

### 6. 提交人工反馈

`POST /tasks/{thread_id}/feedback`

请求体示例一：确认继续

```json
{
  "action": "approve"
}
```

请求体示例二：重新生成分析师

```json
{
  "action": "regenerate",
  "feedback": "请增加一位大学教授背景的分析师"
}
```

说明：

- 只有任务处于 `awaiting_feedback` 时才允许调用
- 当 `action=regenerate` 时，必须提供 `feedback`
- 当 `action=approve` 时，系统会继续执行研究并最终生成报告

### 7. 删除任务

`DELETE /tasks/{thread_id}`

说明：

- 删除任务记录
- 同时清理该任务的运行时进度

## 推荐调用顺序

```text
1. POST   /tasks
2. POST   /tasks/{thread_id}/analysts
3. GET    /tasks/{thread_id}
4. POST   /tasks/{thread_id}/feedback
5. 轮询：
   - GET /tasks/{thread_id}/progress
   - GET /tasks/{thread_id}
6. 完成后从 final_report 读取最终报告
```

## 已移除接口

以下旧接口已下线，不再作为正式能力保留：

- `POST /tasks/{thread_id}/execute`
- `GET /{thread_id}/events`

## 相关实现文件

- 接口定义：`app/api/v1/endpoints/deep_research.py`
- 服务实现：`app/ai/deep_research/service.py`
- 数据模型：`app/schemas/deep_research.py`
