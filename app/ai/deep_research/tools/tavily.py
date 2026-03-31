"""Tavily 搜索工具"""
from functools import lru_cache

from langchain_tavily import TavilySearch
from langchain_tavily.tavily_search import TavilySearchAPIWrapper

from app.ai.deep_research.config import get_config
from app.core.config import settings


@lru_cache
def get_tavily_tool() -> TavilySearch:
    """获取Tavily搜索工具 - 懒加载"""
    config = get_config()
    return TavilySearch(
        max_results=config.tavily_max_results,
        include_answer=True,
        include_raw_content=False,
        api_wrapper=TavilySearchAPIWrapper(tavily_api_key=settings.TAVILY_API_KEY),
    )
