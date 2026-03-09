"""
用户画像Schema
"""
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class BackgroundInfo(BaseModel):
    """背景信息"""
    education: Optional[str] = None
    major: Optional[str] = None
    work_experience: Optional[str] = None


class UserProfileBase(BaseModel):
    """用户画像基础Schema"""
    name: Optional[str] = Field(None, max_length=100, description="姓名")
    age: Optional[int] = Field(None, ge=10, le=100, description="年龄")
    occupation: Optional[str] = Field(None, max_length=100, description="职业")
    technical_background: Optional[Dict[str, Any]] = Field(None, description="技术背景")
    learning_goal: Optional[str] = Field(None, description="学习目标")
    learning_preference: Optional[Dict[str, Any]] = Field(None, description="学习偏好")
    current_level: Optional[Dict[str, Any]] = Field(None, description="当前水平")
    bio: Optional[str] = Field(None, max_length=500, description="简介")


class UserProfileCreate(UserProfileBase):
    """创建用户画像Schema"""
    pass


class UserProfileUpdate(BaseModel):
    """
    更新用户画像Schema

    支持前端格式的字段名，内部自动转换为后端格式
    """
    # 后端原生字段
    name: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=10, le=100)
    occupation: Optional[str] = Field(None, max_length=100)
    technical_background: Optional[Dict[str, Any]] = None
    learning_goal: Optional[str] = None
    learning_preference: Optional[Dict[str, Any]] = None
    current_level: Optional[Dict[str, Any]] = None
    bio: Optional[str] = Field(None, max_length=500)

    # 前端兼容字段
    background: Optional[Dict[str, Any]] = Field(None, description="前端格式的背景信息")
    tech_stack: Optional[List[str]] = Field(None, description="前端格式的技术栈")
    learning_style: Optional[str] = Field(None, description="前端格式的学习风格")

    @model_validator(mode='before')
    @classmethod
    def convert_frontend_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """将前端格式字段转换为后端格式"""
        if not isinstance(values, dict):
            return values

        # 转换 background + tech_stack -> technical_background
        background = values.get('background')
        tech_stack = values.get('tech_stack')

        if background or tech_stack:
            technical_bg = values.get('technical_background') or {}
            if background:
                technical_bg['education'] = background.get('education')
                technical_bg['major'] = background.get('major')
                technical_bg['work_experience'] = background.get('work_experience')
            if tech_stack:
                technical_bg['tech_stack'] = tech_stack
            values['technical_background'] = technical_bg

        # 转换 learning_style -> learning_preference
        learning_style = values.get('learning_style')
        if learning_style:
            learning_pref = values.get('learning_preference') or {}
            learning_pref['style'] = learning_style
            values['learning_preference'] = learning_pref

        return values


class UserProfileResponse(BaseModel):
    """
    用户画像响应Schema

    同时返回后端格式和前端格式的字段
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    # 后端原生字段
    name: Optional[str] = None
    age: Optional[int] = None
    occupation: Optional[str] = None
    technical_background: Optional[Dict[str, Any]] = None
    learning_goal: Optional[str] = None
    learning_preference: Optional[Dict[str, Any]] = None
    current_level: Optional[Dict[str, Any]] = None
    bio: Optional[str] = None

    # 前端兼容字段（自动从后端字段转换）
    background: Optional[Dict[str, Any]] = None
    tech_stack: Optional[List[str]] = None
    learning_style: Optional[str] = None

    @model_validator(mode='after')
    def convert_to_frontend_fields(self):
        """将后端格式字段转换为前端格式"""
        # technical_background -> background + tech_stack
        if self.technical_background:
            self.background = {
                'education': self.technical_background.get('education', ''),
                'major': self.technical_background.get('major', ''),
                'work_experience': self.technical_background.get('work_experience', '')
            }
            self.tech_stack = self.technical_background.get('tech_stack', [])
        else:
            self.background = {'education': '', 'major': '', 'work_experience': ''}
            self.tech_stack = []

        # learning_preference -> learning_style
        if self.learning_preference:
            self.learning_style = self.learning_preference.get('style', 'project_driven')
        else:
            self.learning_style = 'project_driven'

        return self


class ProfileGenerateRequest(BaseModel):
    """
    自动生成画像请求
    
    如果不提供conversation_text，将自动从最近的对话中提取
    """
    conversation_text: Optional[str] = Field(None, description="对话文本（可选，为空则自动提取）")
    limit: int = Field(10, ge=1, le=50, description="提取对话的最大消息数")


class ProfileGenerateResponse(BaseModel):
    """自动生成画像响应"""
    profile: UserProfileResponse
    extracted_info: Dict[str, Any] = Field(..., description="提取的信息")
