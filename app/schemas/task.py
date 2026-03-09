"""
任务Schema
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    """任务基础Schema"""
    title: str = Field(..., max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="优先级")
    due_date: Optional[datetime] = Field(None, description="截止日期")


class TaskCreate(TaskBase):
    """创建任务Schema"""
    learning_path_id: Optional[int] = Field(None, description="关联的学习路径ID")


class TaskUpdate(BaseModel):
    """更新任务Schema"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None


class TaskResponse(TaskBase):
    """任务响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    learning_path_id: Optional[int]
    status: TaskStatus
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskResponse]
    total: int
