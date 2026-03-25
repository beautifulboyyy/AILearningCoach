"""Deep Research Pydantic Schemas"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class AnalystSchema(BaseModel):
    """分析师模型"""
    name: str
    affiliation: str
    role: str
    description: str


class StartResearchRequest(BaseModel):
    """开始研究请求"""
    topic: str = Field(..., min_length=1, max_length=500)
    max_analysts: int = Field(default=3, ge=1, le=5)
    analyst_directions: Optional[List[str]] = None


class ResearchTaskResponse(BaseModel):
    """研究任务响应"""
    id: UUID
    thread_id: str
    topic: str
    status: str
    max_analysts: int
    max_turns: int
    final_report: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HumanFeedbackRequest(BaseModel):
    """人类反馈请求"""
    feedback: Optional[str] = None  # None表示确认满意，继续执行


class SSEResponse(BaseModel):
    """SSE事件数据"""
    event: str
    data: dict
