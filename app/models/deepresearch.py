"""
DeepResearch 持久化模型
"""
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class DeepResearchTaskStatus(str, enum.Enum):
    """DeepResearch 任务状态"""

    PENDING = "pending"
    DRAFTING_ANALYSTS = "drafting_analysts"
    WAITING_FEEDBACK = "waiting_feedback"
    RUNNING_RESEARCH = "running_research"
    COMPLETED = "completed"
    FAILED = "failed"


class DeepResearchPhase(str, enum.Enum):
    """DeepResearch 阶段"""

    ANALYST_GENERATION = "analyst_generation"
    ANALYST_FEEDBACK = "analyst_feedback"
    RESEARCH_EXECUTION = "research_execution"
    REPORT_FINALIZATION = "report_finalization"


class DeepResearchTask(Base, TimestampMixin):
    """DeepResearch 主任务表"""

    __tablename__ = "deep_research_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(500), nullable=False)
    requirements = Column(Text, nullable=True)
    status = Column(
        SQLEnum(DeepResearchTaskStatus),
        default=DeepResearchTaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    phase = Column(SQLEnum(DeepResearchPhase), nullable=True)
    progress_percent = Column(Integer, nullable=False, default=0)
    progress_message = Column(String(255), nullable=True)
    current_revision = Column(Integer, nullable=False, default=0)
    feedback_round_used = Column(Integer, nullable=False, default=0)
    max_feedback_rounds = Column(Integer, nullable=False, default=3)
    selected_revision = Column(Integer, nullable=True)
    final_report_markdown = Column(Text, nullable=True)
    final_report_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    revisions = relationship(
        "DeepResearchAnalystRevision",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    runs = relationship(
        "DeepResearchRun",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<DeepResearchTask(id={self.id}, user_id={self.user_id}, status={self.status})>"


class DeepResearchAnalystRevision(Base, TimestampMixin):
    """分析师草案版本表"""

    __tablename__ = "deep_research_analyst_revisions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("deep_research_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    feedback_text = Column(Text, nullable=True)
    analysts_json = Column(JSON, nullable=True)
    is_selected = Column(Boolean, nullable=False, default=False)

    task = relationship("DeepResearchTask", back_populates="revisions")

    def __repr__(self):
        return (
            f"<DeepResearchAnalystRevision(id={self.id}, task_id={self.task_id}, "
            f"revision_number={self.revision_number})>"
        )


class DeepResearchRun(Base, TimestampMixin):
    """正式研究执行记录表"""

    __tablename__ = "deep_research_runs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("deep_research_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    progress_percent = Column(Integer, nullable=False, default=0)
    progress_message = Column(String(255), nullable=True)
    result_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    task = relationship("DeepResearchTask", back_populates="runs")

    def __repr__(self):
        return f"<DeepResearchRun(id={self.id}, task_id={self.task_id}, revision_number={self.revision_number})>"
