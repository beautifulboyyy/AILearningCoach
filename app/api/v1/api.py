"""
API v1 路由汇总
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, profile, memory, learning_path, task, progress, agents, deep_research

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 对话相关路由
api_router.include_router(chat.router, prefix="/chat", tags=["对话"])

# Agent管理路由
api_router.include_router(agents.router, prefix="/agents", tags=["Agent管理"])

# 用户画像路由
api_router.include_router(profile.router, prefix="/profile", tags=["用户画像"])

# 记忆管理路由
api_router.include_router(memory.router, prefix="/memories", tags=["记忆管理"])

# 学习路径路由
api_router.include_router(learning_path.router, prefix="/learning-path", tags=["学习路径"])

# 任务管理路由
api_router.include_router(task.router, prefix="/tasks", tags=["任务管理"])

# 学习进度路由
api_router.include_router(progress.router, prefix="/progress", tags=["学习进度"])

# 深度研究路由
api_router.include_router(deep_research.router, prefix="/deep-research", tags=["深度研究"])
