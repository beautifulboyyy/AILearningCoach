"""
DeepResearch AI 领域模型
"""
from pydantic import BaseModel, Field


class DeepResearchAnalystProfile(BaseModel):
    """分析师结构化配置"""

    affiliation: str = Field(..., description="分析师所属机构")
    name: str = Field(..., description="分析师姓名")
    role: str = Field(..., description="分析师角色")
    description: str = Field(..., description="分析师关注点描述")
