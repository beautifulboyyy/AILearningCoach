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