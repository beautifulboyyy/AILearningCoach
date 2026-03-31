"""ResearchTask 数据库模型"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Text, Integer, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSON

from app.db.base import Base


class ResearchStatus(str, PyEnum):
    PENDING = "pending"
    AWAITING_FEEDBACK = "awaiting_feedback"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchTask(Base):
    """研究任务模型"""

    __tablename__ = "research_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(String(255), unique=True, nullable=False, index=True)
    topic = Column(String(500), nullable=False)

    status = Column(
        Enum(ResearchStatus, name="research_status"),
        default=ResearchStatus.PENDING,
        nullable=False
    )

    max_analysts = Column(Integer, default=5)
    max_turns = Column(Integer, default=3)
    analysts_config = Column(JSON, nullable=True)

    final_report = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
