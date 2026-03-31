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
    schema = BochaSearchInput.model_json_schema()
    assert "query" in schema["properties"]
    assert "count" in schema["properties"]
