# Deep Research 功能设计文档

> **Goal:** 实现基于LangGraph的Deep Research功能，用户提供话题，多Agent工作流经过探讨检索生成综合报告

## 概述

Deep Research是一个独立的深度研究模块，基于LangGraph框架实现多Agent协作研究工作流。用户输入研究主题，系统自动生成分析师团队，通过并行访谈和检索，最终生成结构化研究报告。

## 技术栈

- **框架**: LangChain + LangGraph
- **LLM**: 通义千问 (ChatTongyi) via `langchain-tongyi`
- **搜索**: Tavily Search + Bocha Search (Custom Tool)
- **存储**: PostgreSQL (任务记录) + Redis (可选缓存) + LangGraph MemorySaver
- **API**: FastAPI + SSE流式输出
- **配置**: .env (DASHSCOPE_API_KEY, BOCHA_API_KEY)

## 架构

### 工作流图

```
START → create_analysts → human_feedback → [Send() 并行] → conduct_interview
                                                              ↓
                                              ask_question → [search_tavily + search_bocha]
                                                              ↓
                                                      answer_question → route
                                                              ↓
                                                      save_interview + write_section
                                                              ↓
                                         [并行] write_report + write_introduction + write_conclusion
                                                              ↓
                                                       finalize_report → SSE Output
```

### 并行度配置

- `max_analysts = 5` (最大分析师数量)
- `max_turns = 3` (每个访谈最大轮次)

### 状态定义

**GenerateAnalystsState** (分析师生成阶段)
```python
{
    "topic": str,                    # 研究主题
    "max_analysts": int,             # 最大分析师数量
    "human_analyst_feedback": str,   # 人类反馈(可选)
    "analysts": List[Analyst]        # 生成的分析师列表
}
```

**InterviewState** (访谈子图)
```python
{
    "messages": List[BaseMessage],   # 对话历史
    "max_num_turns": int,            # 最大对话轮次
    "context": Annotated[list, operator.add],  # 检索到的文档
    "analyst": Analyst,              # 当前分析师
    "interview": str,                 # 完整访谈记录
    "sections": list                  # 访谈摘要小节
}
```

**ResearchGraphState** (主图状态)
```python
{
    "topic": str,
    "max_analysts": int,
    "human_analyst_feedback": str,
    "analysts": List[Analyst],
    "sections": Annotated[list, operator.add],  # 所有小节(累加)
    "introduction": str,
    "content": str,
    "conclusion": str,
    "final_report": str
}
```

### 路由逻辑

**访谈子图路由 (`route_messages`)**
```
条件:
  - 如果专家回答次数 >= max_num_turns → save_interview
  - 如果上一条消息包含"非常感谢您的帮助!" → save_interview
  - 否则 → ask_question (继续提问)
```

**主图条件边**
```
human_feedback:
  - 如果 human_analyst_feedback 有值 → create_analysts (重新生成)
  - 如果为 None → [Send() 并行启动 conduct_interview]
```

### 错误处理

- **API调用失败**: 重试3次，间隔2秒 Exponential backoff
- **搜索无结果**: 继续流程，使用空context
- **LLM生成失败**: 返回错误状态，更新数据库 status=failed
- **任务取消**: 检查 cancelled 状态，提前终止子图执行
- **超时处理**: 全局超时30分钟，超时强制结束

## 目录结构

```
app/ai/deep_research/
├── __init__.py
├── config.py           # 并行度配置
├── state.py            # 状态定义 (GenerateAnalystsState, InterviewState, ResearchGraphState)
├── prompts.py          # 提示词模板
├── tools/
│   ├── __init__.py
│   ├── tavily.py       # Tavily搜索Tool
│   └── bocha.py        # Bocha搜索Custom Tool
├── nodes.py            # 节点函数
├── graph_builder.py    # 图构建
└── service.py          # 服务层

app/api/v1/endpoints/
└── deep_research.py    # API端点

app/models/
└── research_task.py    # SQLAlchemy模型

app/schemas/
└── deep_research.py    # Pydantic schemas
```

## API设计

### 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/deep-research/start` | 开始新研究 |
| GET | `/api/v1/deep-research` | 任务列表 |
| GET | `/api/v1/deep-research/{thread_id}` | 任务详情 |
| GET | `/api/v1/deep-research/{thread_id}/events` | SSE流式事件 |
| POST | `/api/v1/deep-research/{thread_id}/feedback` | 人类反馈 |
| DELETE | `/api/v1/deep-research/{thread_id}` | 取消任务 |

### 请求/响应

**POST /api/v1/deep-research/start**
```json
{
    "topic": "LangGraph的优势分析",
    "max_analysts": 3,
    "analyst_directions": ["技术视角", "商业视角", "用户体验"]
}
```

**GET /api/v1/deep-research/{thread_id}/events (SSE)**
```
event: status
data: {"message": "正在生成分析师..."}

event: analysts
data: {"analysts": [...]}

event: interview_progress
data: {"analyst": "Dr. Emily", "progress": 1}

event: section
data: {"analyst": "Dr. Emily", "section": "## 技术优势..."}

event: report
data: {"content": "报告片段..."}

event: done
data: {"final_report": "完整报告..."}
```

## 数据模型

### ResearchTask (SQLAlchemy)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| thread_id | String | LangGraph thread_id |
| topic | String | 研究主题 |
| status | Enum | pending/running/completed/failed/cancelled |
| max_analysts | Integer | 最大分析师数 |
| max_turns | Integer | 最大访谈轮次 |
| analysts_config | JSON | 分析师配置 |
| final_report | Text | 最终报告 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 核心功能点

### 1. 分析师生成
- 根据主题和方向生成N个分析师
- **单点人类反馈**: 在分析师生成后、人工作审核调整，可选择重新生成或继续
- 使用Pydantic模型结构化输出

### 2. 并行访谈子图
- 每个分析师独立运行访谈子图
- 并行执行search_web (Tavily) 和 search_bocha
- 多轮对话后保存访谈记录

### 3. Map-Reduce归约
- Send() API并行启动多个子图
- write_report/write_introduction/write_conclusion并行执行
- finalize_report整合最终报告

### 4. 流式输出
- SSE实时推送中间结果
- 支持中断点人类反馈
- 任务状态实时更新

## 搜索工具

### Tavily
- 使用 `langchain-tavily` 包
- 配置: `TAVILY_API_KEY`

### Bocha
- Custom Tool封装
- API: `POST https://api.bocha.cn/v1/web-search`
- 认证: `Bearer {API_KEY}`
- 响应格式兼容Bing Search API

## 环境变量

```bash
# .env
DASHSCOPE_API_KEY=sk-xxx          # 通义千问
TAVILY_API_KEY=tvly-xxx           # Tavily
BOCHA_API_KEY=xxx                 # Bocha
```

## 前端(待ui-ux设计)

- 左侧边栏新增"深度研究"菜单
- 主区域展示任务列表和详情
- 支持SSE实时更新
- 位于 `frontend/src/views/deep_research/`
