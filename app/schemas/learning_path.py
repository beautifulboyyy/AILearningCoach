"""
学习路径Schema
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.learning_path import PathStatus
from app.models.progress import ProgressStatus


class Phase(BaseModel):
    """学习阶段"""
    phase: int = Field(..., description="阶段编号")
    weeks: str = Field(..., description="周数，如'1-2'")
    title: str = Field(..., description="阶段标题")
    modules: List[str] = Field(..., description="课程模块列表")
    goal: str = Field(..., description="阶段目标")
    description: Optional[str] = Field(None, description="详细描述")


class LearningPathBase(BaseModel):
    """学习路径基础Schema"""
    title: str = Field(..., max_length=200, description="标题")
    description: Optional[str] = Field(None, description="描述")
    phases: List[Phase] = Field(..., description="学习阶段列表")


class LearningPathCreate(LearningPathBase):
    """创建学习路径Schema"""
    pass


class LearningPathUpdate(BaseModel):
    """更新学习路径Schema"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    phases: Optional[List[Phase]] = None
    status: Optional[PathStatus] = None


class LearningPathResponse(LearningPathBase):
    """学习路径响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: PathStatus
    created_at: datetime
    updated_at: datetime


class GenerateLearningPathRequest(BaseModel):
    """生成学习路径请求"""
    learning_goal: str = Field(..., description="学习目标：job_hunting/project/systematic_learning")
    available_hours_per_week: int = Field(..., ge=1, le=40, description="每周可用学习时间（小时）")
    prior_knowledge: Optional[Dict[str, Any]] = Field(None, description="已有知识背景")
    preferences: Optional[Dict[str, Any]] = Field(None, description="学习偏好")


# ============ 路径模块相关 Schema ============

class PathModuleBase(BaseModel):
    """路径模块基础Schema"""
    phase_index: int = Field(..., description="阶段索引")
    phase_title: Optional[str] = Field(None, description="阶段标题")
    order_index: int = Field(..., description="模块顺序")
    module_key: str = Field(..., max_length=100, description="模块标识")
    module_name: str = Field(..., max_length=200, description="模块名称")
    estimated_hours: float = Field(2.0, description="预计学习时长（小时）")


class PathModuleCreate(PathModuleBase):
    """创建路径模块Schema"""
    learning_path_id: int


class PathModuleResponse(PathModuleBase):
    """路径模块响应Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    learning_path_id: int
    created_at: datetime
    updated_at: datetime


class ModuleProgressDetail(BaseModel):
    """模块进度详情"""
    module_key: str
    module_name: str
    phase_index: int
    phase_title: Optional[str] = None
    completion_percentage: float = 0.0
    actual_hours: float = 0.0
    estimated_hours: float = 2.0
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class PhaseProgressDetail(BaseModel):
    """阶段进度详情"""
    phase_index: int
    phase_title: str
    weeks: str
    goal: str
    completion_percentage: float = 0.0
    modules: List[ModuleProgressDetail] = []
    completed_modules: int = 0
    total_modules: int = 0


class PathProgressResponse(BaseModel):
    """路径进度响应"""
    path_id: int
    path_title: str
    overall_completion: float = 0.0
    status: PathStatus
    phases: List[PhaseProgressDetail] = []
    total_study_hours: float = 0.0
    estimated_total_hours: float = 0.0
    current_module: Optional[ModuleProgressDetail] = None
    next_module: Optional[ModuleProgressDetail] = None
    completed_modules_count: int = 0
    total_modules_count: int = 0
