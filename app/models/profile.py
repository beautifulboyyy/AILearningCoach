"""
用户画像模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    """用户画像表"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # 基本信息
    name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    occupation = Column(String(100), nullable=True)
    
    # 技术背景（JSON格式）
    # 例如: {"programming_languages": ["Python", "JavaScript"], "frameworks": ["FastAPI"], "experience_years": 3}
    technical_background = Column(JSON, nullable=True)
    
    # 学习目标
    learning_goal = Column(String(100), nullable=True)  # "job_hunting", "project", "systematic_learning"
    
    # 学习偏好（JSON格式）
    # 例如: {"content_type": "practical", "explanation_style": "detailed", "learning_pace": "fast"}
    learning_preference = Column(JSON, nullable=True)
    
    # 当前水平（JSON格式）
    # 例如: {"prompt_engineering": "intermediate", "rag": "beginner", "agent": "not_started"}
    current_level = Column(JSON, nullable=True)
    
    # 额外信息
    bio = Column(Text, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, user_id={self.user_id}, name={self.name})>"
