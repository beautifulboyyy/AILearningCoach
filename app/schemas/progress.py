"""
学习进度Schema
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.progress import ProgressStatus, ProgressTriggerType


class ProgressBase(BaseModel):
    """进度基础Schema"""
    module_name: str = Field(..., max_length=100, description="模块名称")
    status: ProgressStatus = Field(ProgressStatus.NOT_STARTED, description="进度状态")
    completion_percentage: float = Field(0.0, ge=0, le=100, description="完成百分比")


class ProgressUpdate(BaseModel):
    """更新进度Schema"""
    status: Optional[ProgressStatus] = None
    completion_percentage: Optional[float] = Field(None, ge=0, le=100)
    actual_hours: Optional[float] = Field(None, ge=0, description="实际学习时长")
    notes: Optional[str] = Field(None, description="学习笔记")


class ProgressResponse(ProgressBase):
    """进度响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    path_module_id: Optional[int] = None
    actual_hours: float = 0.0
    notes: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============ 进度历史相关 Schema ============

class ProgressHistoryBase(BaseModel):
    """进度历史基础Schema"""
    old_percentage: float
    new_percentage: float
    old_status: Optional[ProgressStatus] = None
    new_status: Optional[ProgressStatus] = None
    trigger_type: ProgressTriggerType
    trigger_source: Optional[str] = None
    trigger_detail: Optional[str] = None


class ProgressHistoryResponse(ProgressHistoryBase):
    """进度历史响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    progress_id: int
    created_at: datetime


class ProgressHistoryListResponse(BaseModel):
    """进度历史列表响应"""
    items: List[ProgressHistoryResponse]
    total: int


# ============ 学习活动相关 Schema ============

class RecordActivityRequest(BaseModel):
    """记录学习活动请求"""
    activity_type: str = Field(..., description="活动类型: study/practice/review")
    duration_minutes: int = Field(..., ge=1, le=480, description="活动时长（分钟）")
    notes: Optional[str] = Field(None, description="活动备注")


class RecordActivityResponse(BaseModel):
    """记录学习活动响应"""
    module_key: str
    old_progress: float
    new_progress: float
    progress_change: float
    message: str


class WeeklyTrend(BaseModel):
    """周进度趋势"""
    week: str = Field(..., description="周标识，如W1、W2")
    completion: float = Field(..., description="完成百分比")


class ProgressStatsResponse(BaseModel):
    """进度统计响应"""
    total_modules: int = Field(..., description="总模块数")
    completed_modules: int = Field(..., description="已完成模块数")
    in_progress_modules: int = Field(..., description="进行中模块数")
    not_started_modules: int = Field(..., description="未开始模块数")
    overall_completion: float = Field(..., ge=0, le=100, description="总体完成度")
    current_module: Optional[str] = Field(None, description="当前学习模块")
    # 新增字段
    total_study_hours: float = Field(0.0, description="总学习时长（小时）")
    completed_tasks: int = Field(0, description="已完成任务数")
    learning_days: int = Field(0, description="本周学习天数")
    average_daily_hours: float = Field(0.0, description="平均每日学习时长")
    week_change_percent: float = Field(0.0, description="周环比变化百分比")
    daily_hours: Dict[str, float] = Field(default_factory=dict, description="本周每日学习时长")
    weekly_trend: List[WeeklyTrend] = Field(default_factory=list, description="最近4周进度趋势")


class WeeklyReportResponse(BaseModel):
    """周报响应"""
    week_start: datetime
    week_end: datetime
    study_hours: float = Field(..., description="学习时长（小时）")
    completed_modules: List[str] = Field(..., description="完成的模块")
    questions_asked: int = Field(..., description="提问数量")
    tasks_completed: int = Field(..., description="完成的任务数")
    difficulty_points: List[str] = Field(..., description="困难点")
    suggestions: List[str] = Field(..., description="改进建议")


class MonthlyReportResponse(BaseModel):
    """月报响应"""
    month_start: datetime
    month_end: datetime
    total_study_hours: float
    completed_modules: List[str]
    projects_completed: List[str]
    skill_improvements: Dict[str, str]
    learning_style: str
    next_steps: List[str]
