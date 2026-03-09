"""
学习路径模型
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin
import enum


class PathStatus(str, enum.Enum):
    """路径状态"""
    ACTIVE = "active"          # 进行中
    COMPLETED = "completed"    # 已完成
    PAUSED = "paused"          # 暂停
    CANCELLED = "cancelled"    # 取消


class LearningPath(Base, TimestampMixin):
    """学习路径表"""
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 阶段信息（JSON格式）
    # 例如: [{"phase": 1, "weeks": "1-2", "title": "Prompt工程", "modules": ["讲03-07"], "goal": "掌握基础"}]
    phases = Column(JSON, nullable=False)

    status = Column(SQLEnum(PathStatus), default=PathStatus.ACTIVE, nullable=False)

    # 关系
    user = relationship("User", back_populates="learning_paths")
    tasks = relationship("Task", back_populates="learning_path", cascade="all, delete-orphan")
    modules = relationship("PathModule", back_populates="learning_path", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LearningPath(id={self.id}, title={self.title}, status={self.status})>"


class PathModule(Base, TimestampMixin):
    """
    路径模块表

    将学习路径的阶段模块结构化存储，便于与学习进度关联
    """
    __tablename__ = "path_modules"

    id = Column(Integer, primary_key=True, index=True)
    learning_path_id = Column(
        Integer,
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 模块位置信息
    phase_index = Column(Integer, nullable=False)  # 所属阶段索引 (0, 1, 2...)
    phase_title = Column(String(200), nullable=True)  # 阶段标题
    order_index = Column(Integer, nullable=False)  # 模块在阶段内的顺序

    # 模块信息
    module_key = Column(String(100), nullable=False)  # 模块标识 (如 "lecture_03")
    module_name = Column(String(200), nullable=False)  # 模块显示名 (如 "讲03-Prompt基础")

    # 学习预估
    estimated_hours = Column(Float, default=2.0, nullable=False)  # 预计学习时长（小时）

    # 关系
    learning_path = relationship("LearningPath", back_populates="modules")
    progress = relationship(
        "LearningProgress",
        back_populates="path_module",
        uselist=False,  # 一对一关系
        cascade="all, delete-orphan"
    )

    # 唯一约束：同一路径内模块标识唯一
    __table_args__ = (
        # UniqueConstraint 需要显式导入
    )

    def __repr__(self):
        return f"<PathModule(id={self.id}, key={self.module_key}, path_id={self.learning_path_id})>"
