"""Deep Research 图构建"""
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send

from langchain_core.messages import HumanMessage

from app.ai.deep_research.state import InterviewState, ResearchGraphState
from app.ai.deep_research.nodes import (
    create_analysts, human_feedback, generate_question, search_web, search_bocha,
    generate_answer, route_messages, save_interview, write_section,
    write_report, write_introduction, write_conclusion, finalize_report
)


def build_interview_subgraph():
    """构建访谈子图"""
    builder = StateGraph(InterviewState)

    builder.add_node("ask_question", generate_question)
    builder.add_node("dispatch_search", lambda state: {})
    builder.add_node("search_web", search_web)
    builder.add_node("search_bocha", search_bocha)
    builder.add_node("answer_question", generate_answer)
    builder.add_node("save_interview", save_interview)
    builder.add_node("write_section", write_section)

    builder.add_edge(START, "ask_question")
    builder.add_edge("ask_question", "dispatch_search")
    builder.add_conditional_edges(
        "dispatch_search",
        dispatch_searches,
        ["search_web", "search_bocha"]
    )
    builder.add_edge("search_web", "answer_question")
    builder.add_edge("search_bocha", "answer_question")

    builder.add_conditional_edges(
        "answer_question",
        route_messages,
        ["ask_question", "save_interview"]
    )

    builder.add_edge("save_interview", "write_section")
    builder.add_edge("write_section", END)

    return builder.compile()


def dispatch_searches(state: Dict[str, Any]) -> List[Send]:
    """将问题分发到两个并行搜索节点"""
    return [
        Send("search_web", {"messages": state.get("messages", [])}),
        Send("search_bocha", {"messages": state.get("messages", [])}),
    ]


def initiate_all_interviews(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """启动所有并行访谈 - Map步骤"""
    analysts = state.get("analysts")

    # 注意：不要在这里添加 if not analysts 检查！
    # 如果 analysts 为空，应该返回空的 Send 列表，让 graph 自然结束
    # 而不是循环回 create_analysts 导致无限循环

    topic = state["topic"]
    max_num_turns = state.get("max_num_turns", 3)
    sends = [
        Send("conduct_interview", {
            "analyst": analyst,
            "messages": [HumanMessage(content=f"所以你说你在写一篇关于{topic}的文章?")],
            "max_num_turns": max_num_turns,
        })
        for analyst in analysts
    ]
    return sends


def dispatch_interviews(state: Dict[str, Any]) -> Dict[str, Any]:
    """保留访谈分发所需的主图字段，供后续条件路由使用"""
    return {
        "topic": state["topic"],
        "max_num_turns": state.get("max_num_turns", 3),
        "analysts": state.get("analysts", []),
    }


def build_research_graph():
    """构建主研究图"""
    interview_graph = build_interview_subgraph()

    builder = StateGraph(ResearchGraphState)

    builder.add_node("create_analysts", create_analysts)
    builder.add_node("human_feedback", human_feedback)
    builder.add_node("dispatch_interviews", dispatch_interviews)
    builder.add_node("conduct_interview", interview_graph)
    builder.add_node("write_report", write_report)
    builder.add_node("write_introduction", write_introduction)
    builder.add_node("write_conclusion", write_conclusion)
    builder.add_node("finalize_report", finalize_report)

    builder.add_edge(START, "create_analysts")
    builder.add_edge("create_analysts", "human_feedback")

    builder.add_conditional_edges(
        "dispatch_interviews",
        initiate_all_interviews,
        ["conduct_interview"]
    )

    builder.add_edge("conduct_interview", "write_report")
    builder.add_edge("conduct_interview", "write_introduction")
    builder.add_edge("conduct_interview", "write_conclusion")

    builder.add_edge(
        ["write_report", "write_introduction", "write_conclusion"],
        "finalize_report"
    )
    builder.add_edge("finalize_report", END)

    return builder.compile(
        checkpointer=MemorySaver()
    )


# 全局单例
research_graph = build_research_graph()
