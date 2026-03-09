"""
记忆Schema
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.memory import MemoryType


class MemoryBase(BaseModel):
    """记忆基础Schema"""
    content: str = Field(..., description="记忆内容")
    memory_type: MemoryType = Field(..., description="记忆类型")
    importance_score: float = Field(0.5, ge=0, le=1, description="重要性评分")


class MemoryCreate(MemoryBase):
    """创建记忆Schema"""
    pass


class MemoryResponse(MemoryBase):
    """记忆响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    vector_id: Optional[str] = None
    last_accessed: datetime
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MemoryListResponse(BaseModel):
    """记忆列表响应"""
    memories: List[MemoryResponse]
    total: int


class MemorySearchRequest(BaseModel):
    """记忆搜索请求"""
    query: str = Field(..., min_length=1, description="搜索关键词")
    memory_type: Optional[MemoryType] = Field(None, description="记忆类型过滤")
    top_k: int = Field(5, ge=1, le=20, description="返回数量")
