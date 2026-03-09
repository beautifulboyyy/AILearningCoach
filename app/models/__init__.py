"""
数据库模型模块
"""
from app.db.base import Base
from app.models.user import User
from app.models.profile import UserProfile
from app.models.conversation import Conversation, Message, MessageRole
from app.models.memory import Memory, MemoryType
from app.models.learning_path import LearningPath, PathStatus, PathModule
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.progress import LearningProgress, ProgressStatus, ProgressHistory, ProgressTriggerType
from app.models.knowledge import KnowledgeChunk, DifficultyLevel

__all__ = [
    "Base",
    "User",
    "UserProfile",
    "Conversation",
    "Message",
    "MessageRole",
    "Memory",
    "MemoryType",
    "LearningPath",
    "PathStatus",
    "PathModule",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "LearningProgress",
    "ProgressStatus",
    "ProgressHistory",
    "ProgressTriggerType",
    "KnowledgeChunk",
    "DifficultyLevel",
]
