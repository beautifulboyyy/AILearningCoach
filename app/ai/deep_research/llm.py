"""Deep Research LLM初始化"""
import os
from langchain_openai import ChatOpenAI

from app.ai.deep_research.config import get_config


def create_llm():
    """创建LLM实例 - 使用DashScope OpenAI兼容接口"""
    config = get_config()
    return ChatOpenAI(
        model=config.llm_model,
        temperature=config.llm_temperature,
        base_url=config.dashscope_base_url,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    )


# 全局单例
llm = create_llm()
