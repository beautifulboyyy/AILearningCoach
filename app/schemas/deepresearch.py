"""
DeepResearch Schema
"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DeepResearchAnalyst(BaseModel):
    """分析师结构"""

    affiliation: str = Field(..., max_length=200)
    name: str = Field(..., max_length=100)
    role: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)


class DeepResearchTaskCreate(BaseModel):
    """创建 DeepResearch 任务请求"""

    topic: str = Field(..., min_length=1, max_length=500)
    requirements: Optional[str] = Field(None, max_length=2000)
    max_analysts: int = Field(4, ge=1, le=8)


class DeepResearchFeedbackCreate(BaseModel):
    """提交反馈请求"""

    feedback: str = Field(..., min_length=1, max_length=2000)

    @field_validator("feedback")
    @classmethod
    def validate_feedback(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("feedback 不能为空")
        return cleaned


class DeepResearchAnalystRevisionResponse(BaseModel):
    """分析师版本响应"""

    model_config = ConfigDict(from_attributes=True)

    revision_number: int
    feedback_text: Optional[str] = None
    analysts_json: Optional[List[dict[str, Any]]] = None
    is_selected: bool
    created_at: Optional[datetime] = None


class DeepResearchTaskSummary(BaseModel):
    """任务摘要响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    topic: str
    status: Any
    phase: Any = None
    progress_percent: int
    progress_message: Optional[str] = None
    current_revision: int
    feedback_round_used: int
    max_feedback_rounds: int
    selected_revision: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class DeepResearchTaskDetail(DeepResearchTaskSummary):
    """任务详情响应"""

    requirements: Optional[str] = None
    remaining_feedback_rounds: int
    analysts: List[DeepResearchAnalyst] = Field(default_factory=list)
    report_available: bool
    error_message: Optional[str] = None


class DeepResearchReportResponse(BaseModel):
    """报告响应"""

    task_id: int
    topic: str
    report_markdown: str
