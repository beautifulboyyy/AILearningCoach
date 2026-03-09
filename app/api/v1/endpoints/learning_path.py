"""
学习路径相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.learning_path import (
    LearningPathResponse,
    LearningPathUpdate,
    GenerateLearningPathRequest
)
from app.services.learning_path_service import learning_path_service
from app.utils.logger import app_logger

router = APIRouter()


@router.post("/generate", response_model=LearningPathResponse)
async def generate_learning_path(
    request: GenerateLearningPathRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    生成个性化学习路径
    """
    try:
        learning_path = await learning_path_service.generate_learning_path(
            user_id=current_user.id,
            learning_goal=request.learning_goal,
            available_hours=request.available_hours_per_week,
            db=db,
            prior_knowledge=request.prior_knowledge,
            preferences=request.preferences
        )
        
        return learning_path
        
    except Exception as e:
        app_logger.error(f"生成学习路径失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成学习路径失败: {str(e)}"
        )


@router.get("/active", response_model=LearningPathResponse)
async def get_active_learning_path(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前活跃的学习路径
    """
    learning_path = await learning_path_service.get_active_learning_path(
        user_id=current_user.id,
        db=db
    )
    
    if not learning_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无活跃的学习路径，请先生成学习路径"
        )
    
    return learning_path


@router.get("/{path_id}", response_model=LearningPathResponse)
async def get_learning_path(
    path_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定学习路径
    """
    learning_path = await learning_path_service.get_learning_path(
        path_id=path_id,
        user_id=current_user.id,
        db=db
    )
    
    if not learning_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学习路径不存在"
        )
    
    return learning_path


@router.put("/{path_id}", response_model=LearningPathResponse)
async def update_learning_path(
    path_id: int,
    update_data: LearningPathUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新学习路径
    """
    update_dict = update_data.model_dump(exclude_none=True)
    
    learning_path = await learning_path_service.update_learning_path(
        path_id=path_id,
        user_id=current_user.id,
        update_data=update_dict,
        db=db
    )
    
    if not learning_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学习路径不存在"
        )
    
    return learning_path
