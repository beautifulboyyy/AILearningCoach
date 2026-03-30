"""节点函数测试"""
from langchain_core.messages import AIMessage, HumanMessage

from app.ai.deep_research.nodes import finalize_report, route_messages
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


def test_route_messages_stops_after_max_turns():
    """测试专家回答次数达到上限后结束访谈"""
    state = {
        "messages": [
            HumanMessage(content="问题1"),
            AIMessage(content="回答1", name="expert"),
            HumanMessage(content="问题2"),
            AIMessage(content="回答2", name="expert"),
            HumanMessage(content="问题3"),
            AIMessage(content="回答3", name="expert"),
        ],
        "max_num_turns": 3,
    }

    assert route_messages(state) == "save_interview"


def test_route_messages_stops_when_human_message_thanks():
    """测试分析师在上一轮致谢时结束访谈"""
    state = {
        "messages": [
            HumanMessage(content="前置问题"),
            AIMessage(content="前置回答", name="expert"),
            HumanMessage(content="非常感谢您的帮助!"),
            AIMessage(content="不客气", name="expert"),
        ],
        "max_num_turns": 5,
    }

    assert route_messages(state) == "save_interview"


def test_route_messages_continues_when_turns_not_reached():
    """测试未达到结束条件时继续提问"""
    state = {
        "messages": [
            HumanMessage(content="问题"),
            AIMessage(content="回答", name="expert"),
        ],
        "max_num_turns": 3,
    }

    assert route_messages(state) == "ask_question"


def test_finalize_report_strips_insights_and_keeps_sources():
    """测试最终报告会去掉主体中的 Insights 标题并保留 Sources"""
    state = {
        "introduction": "## 引言\n引言内容",
        "content": "## Insights\n主体内容\n## Sources\n[1] https://example.com",
        "conclusion": "## 结论\n结论内容",
    }

    result = finalize_report(state)

    assert result["final_report"].startswith("## 引言")
    assert "主体内容" in result["final_report"]
    assert "## Insights" not in result["final_report"]
    assert "## Sources\n[1] https://example.com" in result["final_report"]
