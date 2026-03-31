"""Deep Research 配置"""
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from functools import lru_cache


class DeepResearchConfig(BaseSettings):
    """Deep Research 并行度配置"""
    model_config = SettingsConfigDict(env_prefix="DEEP_RESEARCH_")

    max_analysts: int = 5  # 最大分析师数量
    max_turns: int = 3    # 每个访谈最大轮次

    # LLM配置 - 使用DashScope OpenAI兼容接口
    llm_model: str = "qwen-plus"  # 通义千问模型
    llm_temperature: float = 0.0
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 搜索配置
    tavily_max_results: int = 3
    bocha_count: int = 10

    # 超时配置
    global_timeout_minutes: int = 30

@lru_cache
def get_config() -> DeepResearchConfig:
    return DeepResearchConfig()
