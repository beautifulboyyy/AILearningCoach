from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Enum, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class PlanStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    target = Column(String)  # e.g., "Find a job", "Build a project"
    status = Column(String, default=PlanStatus.PENDING.value)
    
    milestones = relationship("Milestone", back_populates="plan", cascade="all, delete-orphan")

class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False)
    title = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    description = Column(String)

    plan = relationship("LearningPlan", back_populates="milestones")
    tasks = relationship("Task", back_populates="milestone", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(String)
    deadline = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, completed

    milestone = relationship("Milestone", back_populates="tasks")
