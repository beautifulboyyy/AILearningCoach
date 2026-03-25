"""Deep Research LLM初始化"""
import os
from functools import lru_cache
from langchain_openai import ChatOpenAI

from app.ai.deep_research.config import get_config


@lru_cache
def get_llm():
    """获取LLM实例 - 懒加载"""
    config = get_config()
    return ChatOpenAI(
        model=config.llm_model,
        temperature=config.llm_temperature,
        base_url=config.dashscope_base_url,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    )
