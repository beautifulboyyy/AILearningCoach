"""
任务管理相关API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.task import TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse
)
from app.services.task_service import task_service
from app.utils.logger import app_logger

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建任务
    """
    try:
        task = await task_service.create_task(
            user_id=current_user.id,
            task_data=task_data.model_dump(),
            db=db
        )
        return task
        
    except Exception as e:
        app_logger.error(f"创建任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建任务失败"
        )


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    status_filter: Optional[TaskStatus] = None,
    status: Optional[TaskStatus] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务列表
    """
    effective_status = status_filter or status

    tasks, total = await task_service.get_tasks(
        user_id=current_user.id,
        db=db,
        status=effective_status,
        limit=limit,
        offset=offset
    )
    
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个任务
    """
    task = await task_service.get_task(
        task_id=task_id,
        user_id=current_user.id,
        db=db
    )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    update_data: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新任务
    """
    task = await task_service.update_task(
        task_id=task_id,
        user_id=current_user.id,
        update_data=update_data.model_dump(exclude_none=True),
        db=db
    )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    完成任务
    """
    task = await task_service.complete_task(
        task_id=task_id,
        user_id=current_user.id,
        db=db
    )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除任务
    """
    success = await task_service.delete_task(
        task_id=task_id,
        user_id=current_user.id,
        db=db
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return {"message": "任务已删除"}
