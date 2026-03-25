"""Deep Research 节点函数"""
from typing import Dict, Any, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, get_buffer_string

from app.ai.deep_research.llm import get_llm
from app.ai.deep_research.prompts import (
    analyst_instructions, question_instructions, answer_instructions,
    section_writer_instructions, report_writer_instructions,
    intro_conclusion_instructions, search_instructions
)
from app.ai.deep_research.tools.tavily import get_tavily_tool
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

    # 使用结构化输出 - 直接使用JsonOutputParser
    from langchain_core.output_parsers import JsonOutputParser

    parser = JsonOutputParser()

    # 提示LLM输出JSON格式
    chain = get_llm() | parser

    response = chain.invoke([
        SystemMessage(content=system_msg + "\n\n请以JSON格式输出分析师列表。"),
        HumanMessage(content="生成分析师集合。")
    ])

    # response 已经是dict，直接使用
    analysts = response.get("analysts", [])

    return {"analysts": analysts}


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
    # 生成搜索查询
    search_query_prompt = search_instructions
    messages = state["messages"]

    from langchain_core.output_parsers import JsonOutputParser
    parser = JsonOutputParser()

    # 从对话中提取搜索查询
    query_gen_chain = get_llm() | parser
    search_query = query_gen_chain.invoke([SystemMessage(content=search_query_prompt)] + messages)

    # 执行Tavily搜索
    docs = get_tavily_tool().invoke(search_query.get("search_query", ""))

    formatted = f'\n\n---\n\n{docs}\n\n---'

    return {"context": [formatted]}


def search_bocha(state: Dict[str, Any]) -> Dict[str, Any]:
    """Bocha Web搜索"""
    search_query_prompt = search_instructions
    messages = state["messages"]

    from langchain_core.output_parsers import JsonOutputParser
    parser = JsonOutputParser()

    query_gen_chain = get_llm() | parser
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
    interview = state.get("interview", "")

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
