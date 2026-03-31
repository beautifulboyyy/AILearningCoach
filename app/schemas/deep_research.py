"""Deep Research Pydantic Schemas"""
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
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
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: str
    topic: str
    status: str
    max_analysts: int
    max_turns: int
    analysts: Optional[List[AnalystSchema]] = None
    final_report: Optional[str]
    created_at: datetime
    updated_at: datetime


class GenerateAnalystsResponse(BaseModel):
    """生成分析师后的响应"""
    status: str
    thread_id: str
    analysts: List[AnalystSchema]
    interrupt_required: bool = True


class HumanFeedbackRequest(BaseModel):
    """人类反馈请求"""
    action: Literal["approve", "regenerate"]
    feedback: Optional[str] = None

    @model_validator(mode="after")
    def validate_feedback(self):
        """重新生成时必须提供自然语言反馈。"""
        if self.action == "regenerate" and not (self.feedback or "").strip():
            raise ValueError("feedback is required when action is regenerate")
        return self


class TaskOperationResponse(BaseModel):
    """任务操作响应"""
    status: str
    thread_id: str
    message: str = ""
    analysts: Optional[List[AnalystSchema]] = None
    final_report: str = ""
    sections_count: int = 0
    error: str = ""


class TaskProgressResponse(BaseModel):
    """任务运行时进度响应"""
    thread_id: str
    stage: str
    message: str = ""
    updated_at: str = ""
