"""图构建测试"""
import pytest
from langgraph.types import Command
from langgraph.types import Send

from app.ai.deep_research.graph_builder import (
    build_interview_subgraph,
    build_research_graph,
    dispatch_interviews,
    initiate_all_interviews,
    dispatch_searches,
)


def test_interview_subgraph_compiles():
    """测试访谈子图编译"""
    graph = build_interview_subgraph()
    assert graph is not None


def test_research_graph_compiles():
    """测试主图编译"""
    graph = build_research_graph()
    assert graph is not None


def test_initiate_all_interviews_uses_state_max_num_turns():
    """测试并行访谈启动时使用状态中的最大轮次配置"""
    sends = initiate_all_interviews(
        {
            "topic": "测试主题",
            "max_num_turns": 5,
            "analysts": [
                {"name": "A", "affiliation": "Org", "role": "R", "description": "D"},
            ],
        }
    )

    assert len(sends) == 1
    assert isinstance(sends[0], Send)
    assert sends[0].arg["max_num_turns"] == 5


def test_dispatch_searches_fans_out_to_tavily_and_bocha():
    """测试搜索分发节点会并行指向 Tavily 和 Bocha 搜索节点"""
    sends = dispatch_searches(
        {
            "max_num_turns": 5,
            "messages": [],
            "analyst": {"name": "A", "affiliation": "Org", "role": "R", "description": "D"},
        }
    )

    assert [send.node for send in sends] == ["search_web", "search_bocha"]
    assert all(send.arg == {"messages": []} for send in sends)


def test_dispatch_interviews_keeps_required_fields():
    """测试访谈分发节点会保留后续路由所需字段"""
    result = dispatch_interviews(
        {
            "topic": "测试主题",
            "max_num_turns": 4,
            "analysts": [{"name": "A", "affiliation": "Org", "role": "R", "description": "D"}],
        }
    )

    assert result["topic"] == "测试主题"
    assert result["max_num_turns"] == 4
    assert result["analysts"][0]["name"] == "A"


def test_research_graph_can_resume_within_same_process():
    """测试在同一进程内可继续中断后的研究流程"""
    thread_id = "graph-memory-resume"
    config = {"configurable": {"thread_id": thread_id}}

    graph = build_research_graph()
    first_result = graph.invoke(
        {
            "topic": "测试进程内恢复",
            "max_analysts": 1,
            "max_num_turns": 1,
            "human_analyst_feedback": "",
        },
        config,
    )

    assert "__interrupt__" in first_result

    final_result = graph.invoke(
        Command(resume={"action": "approve"}),
        config,
    )

    assert final_result["final_report"].strip()
