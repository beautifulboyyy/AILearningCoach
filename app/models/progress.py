"""
学习进度模型
"""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin
import enum


class ProgressStatus(str, enum.Enum):
    """进度状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ProgressTriggerType(str, enum.Enum):
    """进度更新触发类型"""
    MANUAL = "manual"              # 用户手动标记
    CONVERSATION = "conversation"  # 对话内容触发
    TASK_COMPLETE = "task"         # 任务完成触发
    TIME_BASED = "time"            # 学习时长触发
    QUIZ_RESULT = "quiz"           # 测验结果触发
    AI_ASSESSMENT = "ai"           # AI评估触发
    SYSTEM = "system"              # 系统自动（如同步创建）


class LearningProgress(Base, TimestampMixin):
    """学习进度表"""
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 关联到路径模块（可选，用于与学习路径关联）
    path_module_id = Column(
        Integer,
        ForeignKey("path_modules.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    module_name = Column(String(100), nullable=False)  # 例如: "讲14-RAG系统"
    status = Column(SQLEnum(ProgressStatus), default=ProgressStatus.NOT_STARTED, nullable=False)
    completion_percentage = Column(Float, default=0.0, nullable=False)  # 0-100

    # 学习时长统计
    actual_hours = Column(Float, default=0.0, nullable=False)  # 实际学习时长（小时）

    # 学习笔记
    notes = Column(Text, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    user = relationship("User", back_populates="learning_progress")
    path_module = relationship("PathModule", back_populates="progress")
    history = relationship("ProgressHistory", back_populates="progress", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LearningProgress(id={self.id}, module={self.module_name}, completion={self.completion_percentage}%)>"


class ProgressHistory(Base):
    """
    进度变更历史表

    记录每次进度变更的详细信息，用于追溯和分析
    """
    __tablename__ = "progress_history"

    id = Column(Integer, primary_key=True, index=True)
    progress_id = Column(
        Integer,
        ForeignKey("learning_progress.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 变更信息
    old_percentage = Column(Float, nullable=False)  # 变更前百分比
    new_percentage = Column(Float, nullable=False)  # 变更后百分比
    old_status = Column(SQLEnum(ProgressStatus), nullable=True)  # 变更前状态
    new_status = Column(SQLEnum(ProgressStatus), nullable=True)  # 变更后状态

    # 触发信息
    trigger_type = Column(
        SQLEnum(
            ProgressTriggerType,
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        nullable=False
    )  # 触发类型（使用枚举value: manual/time/...）
    trigger_source = Column(String(200), nullable=True)  # 触发来源（如 conversation_id）
    trigger_detail = Column(Text, nullable=True)  # 触发详情（JSON格式的额外信息）

    # 时间戳（不使用 TimestampMixin，只需要创建时间）
    created_at = Column(DateTime, nullable=False, server_default="now()")

    # 关系
    progress = relationship("LearningProgress", back_populates="history")

    def __repr__(self):
        return f"<ProgressHistory(id={self.id}, {self.old_percentage}% -> {self.new_percentage}%)>"
