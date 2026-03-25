# Deep Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现基于LangGraph的Deep Research功能，多Agent工作流并行访谈检索生成综合报告

**Architecture:** 使用LangGraph构建多Agent协作工作流，通过Send() API并行启动访谈子图，使用SSE流式输出。ChatTongyi作为LLM，Tavily和Bocha作为搜索工具。

**Tech Stack:** LangChain, LangGraph, ChatTongyi, Tavily Search, Bocha Search, FastAPI, SQLAlchemy

---

## 任务分解

### Task 1: 项目初始化和依赖安装

**Files:**
- Modify: `requirements.txt`
- Create: `.env.example`

- [ ] **Step 1: 添加依赖到requirements.txt**

```txt
# Deep Research 依赖
langchain-tongyi>=0.2.0
langchain-tavily>=0.3.0
tenacity>=8.2.3
```

- [ ] **Step 2: 创建.env.example**

```bash
# Deep Research
DASHSCOPE_API_KEY=your_dashscope_api_key
TAVILY_API_KEY=your_tavily_api_key
BOCHA_API_KEY=your_bocha_api_key
```

- [ ] **Step 3: 安装依赖**

Run: `pip install langchain-tongyi langchain-tavily tenacity`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt .env.example
git commit -m "deps: 添加 Deep Research 依赖 (langchain-tongyi, langchain-tavily)"
```

---

### Task 2: 创建目录结构和基础配置

**Files:**
- Create: `app/ai/deep_research/__init__.py`
- Create: `app/ai/deep_research/config.py`
- Create: `app/ai/deep_research/tools/__init__.py`

- [ ] **Step 1: 创建config.py**

```python
"""Deep Research 配置"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class DeepResearchConfig(BaseSettings):
    """Deep Research 并行度配置"""

    max_analysts: int = 5  # 最大分析师数量
    max_turns: int = 3    # 每个访谈最大轮次

    # LLM配置
    llm_model: str = "qwen-plus"  # 通义千问模型
    llm_temperature: float = 0.0

    # 搜索配置
    tavily_max_results: int = 3
    bocha_count: int = 10

    # 超时配置
    global_timeout_minutes: int = 30

    class Config:
        env_prefix = "DEEP_RESEARCH_"


@lru_cache
def get_config() -> DeepResearchConfig:
    return DeepResearchConfig()
```

- [ ] **Step 2: Commit**

```bash
git add app/ai/deep_research/
git commit -m "feat: 创建 Deep Research 目录结构和配置"
```

---

### Task 3: 数据模型

**Files:**
- Create: `app/models/research_task.py`
- Modify: `app/models/__init__.py`

- [ ] **Step 1: 创建ResearchTask模型**

```python
"""ResearchTask 数据库模型"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Text, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSON

from app.db.base import Base


class ResearchStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchTask(Base):
    """研究任务模型"""

    __tablename__ = "research_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(String(255), unique=True, nullable=False, index=True)
    topic = Column(String(500), nullable=False)

    status = Column(
        Enum(ResearchStatus, name="research_status"),
        default=ResearchStatus.PENDING,
        nullable=False
    )

    max_analysts = Column(Integer, default=5)
    max_turns = Column(Integer, default=3)
    analysts_config = Column(JSON, nullable=True)

    final_report = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 更新models/__init__.py**

```python
from app.models.research_task import ResearchTask, ResearchStatus
```

- [ ] **Step 3: Commit**

```bash
git add app/models/research_task.py app/models/__init__.py
git commit -m "feat: 添加 ResearchTask 数据库模型"
```

---

### Task 4: Pydantic Schemas

**Files:**
- Create: `app/schemas/deep_research.py`

- [ ] **Step 1: 创建Schemas**

```python
"""Deep Research Pydantic Schemas"""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from uuid import UUID


class AnalystSchema(BaseModel):
    """分析师模型"""
    name: str
    affiliation: str
    role: str
    description: str


class StartResearchRequest(BaseModel):
    """开始研究请求"""
    topic: str = Field(..., min_length=1, max_length=500)
    max_analysts: int = Field(default=3, ge=1, le=5)
    analyst_directions: Optional[List[str]] = None


class ResearchTaskResponse(BaseModel):
    """研究任务响应"""
    id: UUID
    thread_id: str
    topic: str
    status: str
    max_analysts: int
    max_turns: int
    final_report: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HumanFeedbackRequest(BaseModel):
    """人类反馈请求"""
    feedback: Optional[str] = None  # None表示确认满意，继续执行


class SSEResponse(BaseModel):
    """SSE事件数据"""
    event: str
    data: dict
```

- [ ] **Step 2: Commit**

```bash
git add app/schemas/deep_research.py
git commit -m "feat: 添加 Deep Research Pydantic Schemas"
```

---

### Task 5: 状态定义

**Files:**
- Create: `app/ai/deep_research/state.py`

- [ ] **Step 1: 创建state.py**

```python
"""Deep Research 状态定义"""
import operator
from typing import Annotated, List, TypedDict

from langchain_core.messages import BaseMessage


class Analyst(TypedDict):
    """分析师数据模型"""
    name: str
    affiliation: str
    role: str
    description: str


class GenerateAnalystsState(TypedDict):
    """分析师生成状态"""
    topic: str
    max_analysts: int
    human_analyst_feedback: str
    analysts: List[Analyst]


class InterviewState(TypedDict):
    """访谈子图状态"""
    messages: Annotated[List[BaseMessage], operator.add]
    max_num_turns: int
    context: Annotated[list, operator.add]
    analyst: Analyst
    interview: str
    sections: list


class ResearchGraphState(TypedDict):
    """主图状态"""
    topic: str
    max_analysts: int
    human_analyst_feedback: str
    analysts: List[Analyst]
    sections: Annotated[list, operator.add]
    introduction: str
    content: str
    conclusion: str
    final_report: str
```

- [ ] **Step 2: Commit**

```bash
git add app/ai/deep_research/state.py
git commit -m "feat: 添加 Deep Research 状态定义"
```

---

### Task 6: 搜索工具 - Bocha

**Files:**
- Create: `app/ai/deep_research/tools/bocha.py`

- [ ] **Step 1: 创建Bocha搜索工具**

```python
"""Bocha 搜索工具"""
import os
from typing import List, Optional

import httpx
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class BochaSearchInput(BaseModel):
    """Bocha搜索输入"""
    query: str = Field(description="搜索查询")
    count: int = Field(default=10, ge=1, le=50)
    freshness: str = Field(default="noLimit")
    summary: bool = Field(default=False)


class BochaSearchOutput(BaseModel):
    """Bocha搜索输出"""
    results: List[dict]


class BochaSearchTool(BaseTool):
    """Bocha搜索工具 - Custom Tool"""

    name: str = "bocha_search"
    description: str = "从全网搜索网页信息和链接，返回搜索结果"
    args_schema: type[BaseModel] = BochaSearchInput

    def _search(self, query: str, count: int = 10, freshness: str = "noLimit", summary: bool = False) -> List[dict]:
        """执行Bocha搜索"""
        api_key = os.getenv("BOCHA_API_KEY")
        if not api_key:
            raise ValueError("BOCHA_API_KEY not found in environment")

        url = "https://api.bocha.cn/v1/web-search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "count": count,
            "freshness": freshness,
            "summary": summary
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        # 提取webPages.value
        web_pages = data.get("webPages", {})
        results = web_pages.get("value", [])

        return [
            {
                "url": r.get("url", ""),
                "name": r.get("name", ""),
                "snippet": r.get("snippet", ""),
                "siteName": r.get("siteName", ""),
            }
            for r in results
        ]

    def _run(self, query: str, count: int = 10, freshness: str = "noLimit", summary: bool = False) -> str:
        """同步执行搜索"""
        results = self._search(query, count, freshness, summary)
        formatted = "\n\n".join([
            f'<Document href="{r["url"]}"/>\n{r["name"]}\n{r["snippet"]}'
            for r in results
        ])
        return formatted

    async def _arun(self, query: str, count: int = 10, freshness: str = "noLimit", summary: bool = False) -> str:
        """异步执行搜索"""
        results = await self._async_search(query, count, freshness, summary)
        formatted = "\n\n".join([
            f'<Document href="{r["url"]}"/>\n{r["name"]}\n{r["snippet"]}'
            for r in results
        ])
        return formatted

    async def _async_search(self, query: str, count: int, freshness: str, summary: bool) -> List[dict]:
        """异步HTTP请求"""
        api_key = os.getenv("BOCHA_API_KEY")
        if not api_key:
            raise ValueError("BOCHA_API_KEY not found in environment")

        url = "https://api.bocha.cn/v1/web-search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "count": count,
            "freshness": freshness,
            "summary": summary
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        web_pages = data.get("webPages", {})
        results = web_pages.get("value", [])

        return [
            {
                "url": r.get("url", ""),
                "name": r.get("name", ""),
                "snippet": r.get("snippet", ""),
                "siteName": r.get("siteName", ""),
            }
            for r in results
        ]
```

- [ ] **Step 2: Commit**

```bash
git add app/ai/deep_research/tools/bocha.py
git commit -m "feat: 添加 Bocha 搜索工具"
```

---

### Task 7: 搜索工具 - Tavily

**Files:**
- Create: `app/ai/deep_research/tools/tavily.py`

- [ ] **Step 1: 创建Tavily搜索工具**

```python
"""Tavily 搜索工具"""
from langchain_tavily import TavilySearch

from app.ai.deep_research.config import get_config


def create_tavily_tool() -> TavilySearch:
    """创建Tavily搜索工具"""
    config = get_config()
    return TavilySearch(
        max_results=config.tavily_max_results,
        include_answer=True,
        include_raw_content=False,
    )


# 全局单例
tavily_tool = create_tavily_tool()
```

- [ ] **Step 2: Commit**

```bash
git add app/ai/deep_research/tools/tavily.py
git commit -m "feat: 添加 Tavily 搜索工具"
```

---

### Task 8: 提示词模板

**Files:**
- Create: `app/ai/deep_research/prompts.py`

- [ ] **Step 1: 创建prompts.py**

```python
"""Deep Research 提示词模板"""

analyst_instructions = """你需要创建一组 AI 分析师人设。请严格遵循以下指引：

1. 先审阅研究主题：
{topic}

2. 查看（可选的）编辑反馈：
{human_analyst_feedback}

3. 基于上述信息，识别最值得关注的主题。

4. 选出前 {max_analysts} 个主题。

5. 为每个主题分配一位分析师。

请以JSON数组格式输出分析师列表。"""


question_instructions = """你是一名分析师，需要通过访谈专家来了解一个具体主题。

你的目标是提炼与该主题相关的「有趣且具体」的洞见。

1. 有趣（Interesting）：让人感到意外或非显而易见的观点。
2. 具体（Specific）：避免泛泛而谈，包含专家提供的具体案例或细节。

以下是你的关注主题与目标设定：
{goals}

请先用符合你人设的名字进行自我介绍，然后提出你的第一个问题。

持续追问，逐步深入，完善你对该主题的理解。

当你认为信息已充分，请以这句话结束访谈：「非常感谢您的帮助!」"""


search_instructions = """你将获得一段分析师与专家之间的对话。

你的目标是基于这段对话，为Web搜索生成一条结构良好的查询语句。

特别关注分析师最后提出的问题。

将这个最终问题转化为结构良好的 Web 搜索查询。"""


answer_instructions = """你是一位被分析师访谈的专家。

以下是分析师的关注领域：{goals}。

你的目标是回答访谈者提出的问题。

回答问题时，请仅使用以下上下文：

{context}

回答须遵循如下要求：
1. 只使用上下文中提供的信息。
2. 不要引入上下文之外的信息。
3. 在涉及具体论断时，请在相应内容旁标注引用来源编号 [1]。
4. 在答案结尾处按顺序列出引用来源，如：[1] Source 1, [2] Source 2。"""


section_writer_instructions = """你是一名资深技术写作者。

你的任务是基于来源文档，撰写一段简洁、易读的报告小节。

标题需要贴合分析师的关注点并具有吸引力：{focus}

要求：
- 使用 Markdown 格式
- 先给出背景/上下文
- 强调访谈中获得的新颖洞见
- 使用数字引用（如 [1]、[2]）
- 控制在约400字以内
- 生成的小节内容必须全部使用中文

参考格式：
### Sources
[1] 链接或文档名"""


report_writer_instructions = """你是一名技术写作者，正在为如下主题撰写报告：

{topic}

你拥有一支分析师团队。每位分析师完成了两件事：
1. 围绕一个具体子主题，访谈了一位专家。
2. 将发现写成一份备忘录。

你的任务：
1. 仔细思考每份备忘录的洞见。
2. 将它们整合为简洁的总体总结。

报告格式要求：
1. 使用 Markdown 格式
2. 报告以一个标题开头：## Insights
3. 汇总最终来源列表，以 ## Sources 作为小节标题
4. 生成的报告必须全部使用中文"""


intro_conclusion_instructions = """你是一名技术写作者，正在完成主题为 {topic} 的报告。

你的任务是撰写简洁而有说服力的引言或结论。

引言小节标题使用：## 引言
结论小节标题使用：## 结论

目标约100字，使用Markdown格式，生成的内容必须全部使用中文。

撰写时可参考以下小节内容：
{formatted_str_sections}"""
```

- [ ] **Step 2: Commit**

```bash
git add app/ai/deep_research/prompts.py
git commit -m "feat: 添加 Deep Research 提示词模板"
```

---

### Task 9: LLM和Tools初始化

**Files:**
- Create: `app/ai/deep_research/llm.py`

- [ ] **Step 1: 创建LLM初始化**

```python
"""Deep Research LLM初始化"""
import os
from langchain_tongyi import ChatTongyi

from app.ai.deep_research.config import get_config


def create_llm():
    """创建ChatTongyi LLM实例"""
    config = get_config()
    return ChatTongyi(
        model=config.llm_model,
        temperature=config.llm_temperature,
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
    )


# 全局单例
llm = create_llm()
```

- [ ] **Step 2: Commit**

```bash
git add app/ai/deep_research/llm.py
git commit -m "feat: 添加 Deep Research LLM 初始化"
```

---

### Task 10: 节点函数

**Files:**
- Create: `app/ai/deep_research/nodes.py`

- [ ] **Step 1: 创建nodes.py**

```python
"""Deep Research 节点函数"""
import json
from typing import List, Dict, Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, get_buffer_string
from langchain_core.outputs import ChatGeneration

from app.ai.deep_research.llm import llm
from app.ai.deep_research.prompts import (
    analyst_instructions, question_instructions, answer_instructions,
    section_writer_instructions, report_writer_instructions,
    intro_conclusion_instructions, search_instructions
)
from app.ai.deep_research.tools.tavily import tavily_tool
from app.ai.deep_research.tools.bocha import BochaSearchTool


bocha_tool = BochaSearchTool()


def create_analysts(state: Dict[str, Any]) -> Dict[str, Any]:
    """创建分析师团队"""
    topic = state["topic"]
    max_analysts = state["max_analysts"]
    human_feedback = state.get("human_analyst_feedback", "")

    system_msg = analyst_instructions.format(
        topic=topic,
        human_analyst_feedback=human_feedback,
        max_analysts=max_analysts
    )

    # 使用结构化输出
    from langchain_core.output_parsers import JsonOutputParser
    from pydantic import BaseModel, Field
    from typing import List as TList

    class AnalystOutput(BaseModel):
        name: str
        affiliation: str
        role: str
        description: str

    class AnalystsOutput(BaseModel):
        analysts: TList[AnalystOutput]

    parser = JsonOutputParser(pydantic_object=AnalystsOutput)
    chain = llm | parser

    response = chain.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content="生成分析师集合，以JSON格式输出。")
    ])

    analysts = [
        {"name": a["name"], "affiliation": a["affiliation"],
         "role": a["role"], "description": a["description"]}
        for a in response["analysts"]
    ]

    return {"analysts": analysts}


def generate_question(state: Dict[str, Any]) -> Dict[str, Any]:
    """生成访谈问题"""
    analyst = state["analyst"]
    messages = state["messages"]

    # 构建人设描述
    persona = f"Name: {analyst['name']}\nRole: {analyst['role']}\nAffiliation: {analyst['affiliation']}\nDescription: {analyst['description']}"

    system_msg = question_instructions.format(goals=persona)
    question = llm.invoke([SystemMessage(content=system_msg)] + messages)

    return {"messages": [question]}


def search_web(state: Dict[str, Any]) -> Dict[str, Any]:
    """Tavily Web搜索"""
    # 生成搜索查询
    search_query_prompt = search_instructions
    messages = state["messages"]

    from langchain_core.output_schemas import JsonOutputParser
    parser = JsonOutputParser()

    # 从对话中提取搜索查询
    query_gen_chain = llm | parser
    search_query = query_gen_chain.invoke([SystemMessage(content=search_query_prompt)] + messages)

    # 执行Tavily搜索
    docs = tavily_tool.invoke(search_query.get("search_query", ""))

    formatted = f'\n\n---\n\n{docs}\n\n---'

    return {"context": [formatted]}


def search_bocha(state: Dict[str, Any]) -> Dict[str, Any]:
    """Bocha Web搜索"""
    search_query_prompt = search_instructions
    messages = state["messages"]

    from langchain_core.output_schemas import JsonOutputParser
    parser = JsonOutputParser()

    query_gen_chain = llm | parser
    search_query = query_gen_chain.invoke([SystemMessage(content=search_query_prompt)] + messages)

    # 执行Bocha搜索
    query = search_query.get("search_query", "")
    docs = bocha_tool._run(query=query, count=10)

    formatted = f'\n\n---\n\n{docs}\n\n---'

    return {"context": [formatted]}


def generate_answer(state: Dict[str, Any]) -> Dict[str, Any]:
    """生成专家回答"""
    analyst = state["analyst"]
    messages = state["messages"]
    context = state.get("context", [])

    persona = f"Name: {analyst['name']}\nRole: {analyst['role']}\nAffiliation: {analyst['affiliation']}\nDescription: {analyst['description']}"

    system_msg = answer_instructions.format(
        goals=persona,
        context="\n".join(context)
    )

    answer = llm.invoke([SystemMessage(content=system_msg)] + messages)
    answer.name = "expert"

    return {"messages": [answer]}


def route_messages(state: Dict[str, Any]) -> str:
    """路由函数"""
    messages = state["messages"]
    max_num_turns = state.get("max_num_turns", 3)

    num_responses = len([
        m for m in messages
        if isinstance(m, AIMessage) and m.name == "expert"
    ])

    if num_responses >= max_num_turns:
        return "save_interview"

    last_msg = messages[-1]
    if isinstance(last_msg, HumanMessage) and "非常感谢您的帮助" in last_msg.content:
        return "save_interview"

    return "ask_question"


def save_interview(state: Dict[str, Any]) -> Dict[str, Any]:
    """保存访谈"""
    messages = state["messages"]
    interview = get_buffer_string(messages)
    return {"interview": interview}


def write_section(state: Dict[str, Any]) -> Dict[str, Any]:
    """撰写报告小节"""
    analyst = state["analyst"]
    context = state.get("context", [])
    interview = state.get("interview", "")

    system_msg = section_writer_instructions.format(focus=analyst["description"])

    section = llm.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=f"使用这些来源撰写你的小节: {context}")
    ])

    return {"sections": [section.content]}


def write_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """撰写报告主体"""
    sections = state["sections"]
    topic = state["topic"]

    formatted = "\n\n".join(sections)
    system_msg = report_writer_instructions.format(topic=topic, context=formatted)

    report = llm.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content="基于这些备忘录撰写报告。")
    ])

    return {"content": report.content}


def write_introduction(state: Dict[str, Any]) -> Dict[str, Any]:
    """撰写引言"""
    sections = state["sections"]
    topic = state["topic"]

    formatted = "\n\n".join(sections)
    instructions = intro_conclusion_instructions.format(
        topic=topic,
        formatted_str_sections=formatted
    )

    intro = llm.invoke([
        SystemMessage(content=instructions),
        HumanMessage(content="撰写报告引言")
    ])

    return {"introduction": intro.content}


def write_conclusion(state: Dict[str, Any]) -> Dict[str, Any]:
    """撰写结论"""
    sections = state["sections"]
    topic = state["topic"]

    formatted = "\n\n".join(sections)
    instructions = intro_conclusion_instructions.format(
        topic=topic,
        formatted_str_sections=formatted
    )

    conclusion = llm.invoke([
        SystemMessage(content=instructions),
        HumanMessage(content="撰写报告结论")
    ])

    return {"conclusion": conclusion.content}


def finalize_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """整合最终报告"""
    content = state["content"]

    if "## Sources" in content:
        try:
            content, sources = content.split("\n## Sources\n")
        except:
            sources = None
    else:
        sources = None

    final_report = (
        state["introduction"] +
        "\n\n---\n\n" +
        content +
        "\n\n---\n\n" +
        state["conclusion"]
    )

    if sources:
        final_report += "\n\n## Sources\n" + sources

    return {"final_report": final_report}
```

- [ ] **Step 2: Commit**

```bash
git add app/ai/deep_research/nodes.py
git commit -m "feat: 添加 Deep Research 节点函数"
```

---

### Task 11: 图构建

**Files:**
- Create: `app/ai/deep_research/graph_builder.py`

- [ ] **Step 1: 创建graph_builder.py**

```python
"""Deep Research 图构建"""
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
from langgraph.checkpoint.memory import MemorySaver

from app.ai.deep_research.state import InterviewState, ResearchGraphState
from app.ai.deep_research.nodes import (
    create_analysts, generate_question, search_web, search_bocha,
    generate_answer, route_messages, save_interview, write_section,
    write_report, write_introduction, write_conclusion, finalize_report
)


def build_interview_subgraph():
    """构建访谈子图"""
    builder = StateGraph(InterviewState)

    builder.add_node("ask_question", generate_question)
    builder.add_node("search_web", search_web)
    builder.add_node("search_bocha", search_bocha)
    builder.add_node("answer_question", generate_answer)
    builder.add_node("save_interview", save_interview)
    builder.add_node("write_section", write_section)

    builder.add_edge(START, "ask_question")
    builder.add_edge("ask_question", "search_web")
    builder.add_edge("ask_question", "search_bocha")
    builder.add_edge("search_web", "answer_question")
    builder.add_edge("search_bocha", "answer_question")

    builder.add_conditional_edges(
        "answer_question",
        route_messages,
        {"ask_question": "ask_question", "save_interview": "save_interview"}
    )

    builder.add_edge("save_interview", "write_section")
    builder.add_edge("write_section", END)

    return builder.compile()


def initiate_all_interviews(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """启动所有并行访谈 - Map步骤"""
    feedback = state.get("human_analyst_feedback")
    if feedback:
        return "create_analysts"

    topic = state["topic"]
    analysts = state["analysts"]

    return [
        Send("conduct_interview", {
            "analyst": analyst,
            "messages": [("user", f"所以你说你在写一篇关于{topic}的文章?")],
            "max_num_turns": 3,
        })
        for analyst in analysts
    ]


def build_research_graph():
    """构建主研究图"""
    interview_graph = build_interview_subgraph()

    builder = StateGraph(ResearchGraphState)

    builder.add_node("create_analysts", create_analysts)
    builder.add_node("human_feedback", lambda state: None)
    builder.add_node("conduct_interview", interview_graph)
    builder.add_node("write_report", write_report)
    builder.add_node("write_introduction", write_introduction)
    builder.add_node("write_conclusion", write_conclusion)
    builder.add_node("finalize_report", finalize_report)

    builder.add_edge(START, "create_analysts")
    builder.add_edge("create_analysts", "human_feedback")

    builder.add_conditional_edges(
        "human_feedback",
        initiate_all_interviews,
        {"create_analysts": "create_analysts", "conduct_interview": "conduct_interview"}
    )

    builder.add_edge("conduct_interview", "write_report")
    builder.add_edge("conduct_interview", "write_introduction")
    builder.add_edge("conduct_interview", "write_conclusion")

    builder.add_edge(
        ["write_report", "write_introduction", "write_conclusion"],
        "finalize_report"
    )
    builder.add_edge("finalize_report", END)

    memory = MemorySaver()
    return builder.compile(
        interrupt_before=["human_feedback"],
        checkpointer=memory
    )


# 全局单例
research_graph = build_research_graph()
```

- [ ] **Step 2: Commit**

```bash
git add app/ai/deep_research/graph_builder.py
git commit -m "feat: 添加 Deep Research 图构建"
```

---

### Task 12: 服务层

**Files:**
- Create: `app/ai/deep_research/service.py`

- [ ] **Step 1: 创建service.py**

```python
"""Deep Research 服务层"""
import uuid
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research_task import ResearchTask, ResearchStatus
from app.schemas.deep_research import StartResearchRequest, HumanFeedbackRequest
from app.ai.deep_research.graph_builder import research_graph
from app.ai.deep_research.config import get_config


class DeepResearchService:
    """Deep Research 服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.config = get_config()

    async def create_task(self, request: StartResearchRequest) -> ResearchTask:
        """创建新研究任务"""
        thread_id = f"research_{uuid.uuid4().hex[:12]}"

        task = ResearchTask(
            thread_id=thread_id,
            topic=request.topic,
            status=ResearchStatus.PENDING,
            max_analysts=request.max_analysts,
            max_turns=self.config.max_turns,
            analysts_config={"directions": request.analyst_directions}
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def get_task_by_thread_id(self, thread_id: str) -> Optional[ResearchTask]:
        """通过thread_id获取任务"""
        result = await self.db.execute(
            select(ResearchTask).where(ResearchTask.thread_id == thread_id)
        )
        return result.scalar_one_or_none()

    async def list_tasks(self, limit: int = 50) -> list[ResearchTask]:
        """获取任务列表"""
        result = await self.db.execute(
            select(ResearchTask)
            .order_by(ResearchTask.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_task_status(self, thread_id: str, status: ResearchStatus, final_report: str = None):
        """更新任务状态"""
        task = await self.get_task_by_thread_id(thread_id)
        if task:
            task.status = status
            if final_report:
                task.final_report = final_report
            await self.db.commit()

    async def submit_feedback(self, thread_id: str, feedback: Optional[str]) -> Dict[str, Any]:
        """提交人类反馈并继续执行"""
        config = {"configurable": {"thread_id": thread_id}}

        if feedback:
            # 有反馈，更新状态
            research_graph.update_state(
                config,
                {"human_analyst_feedback": feedback},
                as_node="human_feedback"
            )
        else:
            # 无反馈，继续执行
            research_graph.update_state(
                config,
                {"human_analyst_feedback": None},
                as_node="human_feedback"
            )

        # 继续执行
        task = await self.get_task_by_thread_id(thread_id)
        if task:
            await self.update_task_status(thread_id, ResearchStatus.RUNNING)

        return {"status": "continued"}

    async def run_research(self, thread_id: str, topic: str, max_analysts: int) -> AsyncGenerator[Dict[str, Any], None]:
        """运行研究工作流"""
        config = {"configurable": {"thread_id": thread_id}}

        # 更新状态为运行中
        await self.update_task_status(thread_id, ResearchStatus.RUNNING)

        initial_state = {
            "topic": topic,
            "max_analysts": max_analysts,
            "human_analyst_feedback": "",
        }

        try:
            async for event in research_graph.astream_events(
                initial_state,
                config,
                stream_mode="values"
            ):
                # 提取事件类型和内容
                event_type = self._classify_event(event)
                if event_type:
                    yield event_type

        except Exception as e:
            await self.update_task_status(thread_id, ResearchStatus.FAILED)
            yield {"type": "error", "data": {"message": str(e)}}

        # 完成
        final_state = research_graph.get_state(config)
        final_report = final_state.values.get("final_report", "")

        await self.update_task_status(
            thread_id,
            ResearchStatus.COMPLETED,
            final_report=final_report
        )

        yield {"type": "done", "data": {"final_report": final_report}}

    def _classify_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分类事件类型"""
        if "create_analysts" in event:
            return {"type": "status", "data": {"message": "正在生成分析师..."}}
        return None
```

- [ ] **Step 2: Commit**

```bash
git add app/ai/deep_research/service.py
git commit -m "feat: 添加 Deep Research 服务层"
```

---

### Task 13: API端点

**Files:**
- Create: `app/api/v1/endpoints/deep_research.py`
- Modify: `app/api/v1/api.py`

- [ ] **Step 1: 创建API端点**

```python
"""Deep Research API端点"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.deps import get_db
from app.schemas.deep_research import (
    StartResearchRequest, ResearchTaskResponse,
    HumanFeedbackRequest
)
from app.ai.deep_research.service import DeepResearchService


router = APIRouter()


@router.post("/start", response_model=ResearchTaskResponse)
async def start_research(
    request: StartResearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """开始新的研究任务"""
    service = DeepResearchService(db)
    task = await service.create_task(request)

    return ResearchTaskResponse.model_validate(task)


@router.get("", response_model=List[ResearchTaskResponse])
async def list_research_tasks(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取研究任务列表"""
    service = DeepResearchService(db)
    tasks = await service.list_tasks(limit)
    return [ResearchTaskResponse.model_validate(t) for t in tasks]


@router.get("/{thread_id}", response_model=ResearchTaskResponse)
async def get_research_task(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取特定研究任务"""
    service = DeepResearchService(db)
    task = await service.get_task_by_thread_id(thread_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return ResearchTaskResponse.model_validate(task)


@router.post("/{thread_id}/feedback")
async def submit_feedback(
    thread_id: str,
    request: HumanFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """提交人类反馈"""
    service = DeepResearchService(db)

    task = await service.get_task_by_thread_id(thread_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    result = await service.submit_feedback(thread_id, request.feedback)
    return result


@router.delete("/{thread_id}")
async def cancel_research(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """取消研究任务"""
    service = DeepResearchService(db)

    task = await service.get_task_by_thread_id(thread_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    from app.models.research_task import ResearchStatus
    await service.update_task_status(thread_id, ResearchStatus.CANCELLED)

    return {"status": "cancelled"}


@router.get("/{thread_id}/events")
async def stream_research_events(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """SSE流式事件"""
    service = DeepResearchService(db)

    task = await service.get_task_by_thread_id(thread_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    async def event_generator():
        async for event in service.run_research(
            thread_id,
            task.topic,
            task.max_analysts
        ):
            yield f"data: {event}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

- [ ] **Step 2: 注册路由到api.py**

```python
# 在 app/api/v1/api.py 中添加
from app.api.v1.endpoints import deep_research

api_router.include_router(deep_research.router, prefix="/deep-research", tags=["深度研究"])
```

- [ ] **Step 3: Commit**

```bash
git add app/api/v1/endpoints/deep_research.py app/api/v1/api.py
git commit -m "feat: 添加 Deep Research API端点"
```

---

### Task 14: 数据库迁移

**Files:**
- Create: `alembic/versions/xxxx_add_research_tasks.py`

- [ ] **Step 1: 创建迁移文件**

```python
"""添加研究任务表"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = 'add_research_tasks'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'research_tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('thread_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('topic', sa.String(500), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='research_status'), nullable=False),
        sa.Column('max_analysts', sa.Integer(), default=5),
        sa.Column('max_turns', sa.Integer(), default=3),
        sa.Column('analysts_config', JSON, nullable=True),
        sa.Column('final_report', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )


def downgrade():
    op.drop_table('research_tasks')
```

- [ ] **Step 2: 运行迁移**

Run: `alembic upgrade head`

- [ ] **Step 3: Commit**

```bash
git add alembic/versions/xxxx_add_research_tasks.py
git commit -m "feat: 添加 research_tasks 表迁移"
```

---

### Task 15: 单元测试

**Files:**
- Create: `tests/ai/deep_research/test_bocha_tool.py`
- Create: `tests/ai/deep_research/test_nodes.py`
- Create: `tests/ai/deep_research/test_graph.py`

- [ ] **Step 1: 测试Bocha工具**

```python
"""Bocha工具测试"""
import pytest
from app.ai.deep_research.tools.bocha import BochaSearchTool


def test_bocha_search_tool_created():
    """测试Bocha工具实例化"""
    tool = BochaSearchTool()
    assert tool.name == "bocha_search"
    assert "搜索" in tool.description


def test_bocha_search_tool_input_schema():
    """测试输入schema"""
    from app.ai.deep_research.tools.bocha import BochaSearchInput
    schema = BochaSearchInput.schema()
    assert "query" in schema["properties"]
    assert "count" in schema["properties"]
```

- [ ] **Step 2: 测试节点函数**

```python
"""节点函数测试"""
import pytest
from app.ai.deep_research.state import GenerateAnalystsState


def test_generate_analysts_state_structure():
    """测试状态结构"""
    state = GenerateAnalystsState(
        topic="测试主题",
        max_analysts=3,
        human_analyst_feedback="",
        analysts=[]
    )
    assert state["topic"] == "测试主题"
    assert state["max_analysts"] == 3
```

- [ ] **Step 3: 测试图构建**

```python
"""图构建测试"""
import pytest
from app.ai.deep_research.graph_builder import build_interview_subgraph, build_research_graph


def test_interview_subgraph_compiles():
    """测试访谈子图编译"""
    graph = build_interview_subgraph()
    assert graph is not None


def test_research_graph_compiles():
    """测试主图编译"""
    graph = build_research_graph()
    assert graph is not None
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/ai/deep_research/ -v`

- [ ] **Step 5: Commit**

```bash
git add tests/ai/deep_research/
git commit -m "test: 添加 Deep Research 单元测试"
```

---

## 执行方式

**Plan complete and saved to `docs/superpowers/plans/2026-03-25-deep-research-plan.md`**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
