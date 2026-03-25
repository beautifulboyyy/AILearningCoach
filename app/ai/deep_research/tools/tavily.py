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
