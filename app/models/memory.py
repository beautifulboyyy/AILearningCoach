"""
记忆模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin
from datetime import datetime
import enum


class MemoryType(str, enum.Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"      # 短期记忆（会话内）
    WORKING = "working"             # 工作记忆（7天）
    LONG_TERM = "long_term"         # 长期记忆（永久）


class Memory(Base, TimestampMixin):
    """记忆表"""
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    memory_type = Column(SQLEnum(MemoryType), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # 向量存储在Milvus中，这里只存储向量ID
    vector_id = Column(String(100), nullable=True, index=True)
    
    # 重要性评分（0-1之间）
    importance_score = Column(Float, default=0.5, nullable=False)
    
    # 最后访问时间（用于时间衰减）
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 过期时间（短期记忆和工作记忆有过期时间）
    expires_at = Column(DateTime, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="memories")
    
    def __repr__(self):
        return f"<Memory(id={self.id}, type={self.memory_type}, user_id={self.user_id})>"
