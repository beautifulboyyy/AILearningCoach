"""
知识库模型
"""
from sqlalchemy import Column, Integer, String, Text, JSON, Enum as SQLEnum
from app.db.base import Base, TimestampMixin
import enum


class DifficultyLevel(str, enum.Enum):
    """难度等级"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class KnowledgeChunk(Base, TimestampMixin):
    """知识块表"""
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 讲义信息
    lecture_number = Column(Integer, nullable=False, index=True)  # 讲义编号，如14
    section = Column(String(50), nullable=True)  # 章节号，如"2.3"
    
    # 内容
    content = Column(Text, nullable=False)
    
    # 向量存储在Milvus中，这里只存储向量ID
    vector_id = Column(String(100), nullable=True, unique=True, index=True)
    
    # 元数据（JSON格式）
    # 例如: {"title": "RAG原理", "keywords": ["RAG", "检索", "生成"], "has_code": true}
    # 注意：不能使用metadata作为字段名（SQLAlchemy保留字）
    meta_info = Column(JSON, nullable=True)
    
    # 难度等级
    difficulty_level = Column(SQLEnum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE, nullable=False)
    
    def __repr__(self):
        return f"<KnowledgeChunk(id={self.id}, lecture={self.lecture_number}, section={self.section})>"
