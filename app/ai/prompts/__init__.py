"""
Prompt模块包
"""
from app.ai.prompts.system_prompts import (
    BASE_SYSTEM_PROMPT,
    RAG_QA_SYSTEM_PROMPT,
    LEARNING_PLANNER_SYSTEM_PROMPT,
    PROJECT_COACH_SYSTEM_PROMPT,
    PROGRESS_ANALYST_SYSTEM_PROMPT,
    get_rag_prompt_with_context
)

__all__ = [
    "BASE_SYSTEM_PROMPT",
    "RAG_QA_SYSTEM_PROMPT",
    "LEARNING_PLANNER_SYSTEM_PROMPT",
    "PROJECT_COACH_SYSTEM_PROMPT",
    "PROGRESS_ANALYST_SYSTEM_PROMPT",
    "get_rag_prompt_with_context"
]
