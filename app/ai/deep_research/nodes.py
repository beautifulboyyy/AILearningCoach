"""Deep Research 节点函数"""
from typing import Dict, Any, List, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, get_buffer_string
from langchain_core.output_parsers import JsonOutputParser

from app.ai.deep_research.llm import get_llm
from app.ai.deep_research.prompts import (
    analyst_instructions, question_instructions, answer_instructions,
    section_writer_instructions, report_writer_instructions,
    intro_conclusion_instructions, search_instructions
)
from app.ai.deep_research.tools.tavily import get_tavily_tool
from app.ai.deep_research.tools.bocha import BochaSearchTool


bocha_tool = BochaSearchTool()


# ===== Pydantic 模型 =====
class Analyst(BaseModel):
    """分析师数据模型"""
    affiliation: str = Field(description="分析师的主要隶属机构或组织")
    name: str = Field(description="分析师姓名")
    role: str = Field(description="分析师在研究主题中的具体角色定位")
    description: str = Field(description="分析师的关注焦点、关切点和动机的详细描述")

    @property
    def persona(self) -> str:
        """生成分析师人设描述"""
        return f"Name: {self.name}\nRole: {self.role}\nAffiliation: {self.affiliation}\nDescription: {self.description}\n"


class Perspectives(BaseModel):
    """分析师集合数据模型"""
    analysts: List[Analyst] = Field(description="包含所有分析师角色和隶属机构的综合列表")


class SearchQuery(BaseModel):
    """搜索查询数据模型"""
    search_query: str = Field(None, description="用于检索的搜索查询语句")


# ===== 节点函数 =====
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

    structured_llm = get_llm().with_structured_output(Perspectives)

    try:
        result = structured_llm.invoke([
            SystemMessage(content=system_msg),
            HumanMessage(content="生成分析师集合。")
        ])
        analysts = result.analysts if result else []
    except Exception:
        analysts = []

    # 转换为字典以兼容checkpoint序列化
    return {"analysts": [a.model_dump() for a in analysts]}


def generate_question(state: Dict[str, Any]) -> Dict[str, Any]:
    """生成访谈问题"""
    analyst = state["analyst"]
    messages = state["messages"]

    # 构建人设描述
    persona = f"Name: {analyst['name']}\nRole: {analyst['role']}\nAffiliation: {analyst['affiliation']}\nDescription: {analyst['description']}"

    system_msg = question_instructions.format(goals=persona)
    question = get_llm().invoke([SystemMessage(content=system_msg)] + messages)

    return {"messages": [question]}


def search_web(state: Dict[str, Any]) -> Dict[str, Any]:
    """Tavily Web搜索"""
    messages = state["messages"]

    structured_llm = get_llm().with_structured_output(SearchQuery)
    search_query = structured_llm.invoke([search_instructions] + messages)

    docs = get_tavily_tool().invoke(search_query.search_query or "")

    formatted = f'\n\n---\n\n{docs}\n\n---'

    return {"context": [formatted]}


def search_bocha(state: Dict[str, Any]) -> Dict[str, Any]:
    """Bocha Web搜索"""
    messages = state["messages"]

    structured_llm = get_llm().with_structured_output(SearchQuery)
    search_query = structured_llm.invoke([search_instructions] + messages)

    docs = bocha_tool._run(query=search_query.search_query or "", count=10)

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

    answer = get_llm().invoke([SystemMessage(content=system_msg)] + messages)
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

    system_msg = section_writer_instructions.format(focus=analyst["description"])

    section = get_llm().invoke([
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

    report = get_llm().invoke([
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

    intro = get_llm().invoke([
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

    conclusion = get_llm().invoke([
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
