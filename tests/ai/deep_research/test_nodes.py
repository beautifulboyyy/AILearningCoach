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
