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
