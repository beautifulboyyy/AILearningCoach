"""
记忆管理相关API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.memory import Memory, MemoryType
from app.schemas.memory import (
    MemoryResponse,
    MemoryListResponse,
    MemorySearchRequest
)
from app.ai.memory.manager import memory_manager
from app.utils.logger import app_logger

router = APIRouter()


@router.get("/", response_model=MemoryListResponse)
async def get_memories(
    memory_type: Optional[MemoryType] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户记忆列表
    """
    try:
        # 构建查询
        query = select(Memory).filter(Memory.user_id == current_user.id)
        
        if memory_type:
            query = query.filter(Memory.memory_type == memory_type)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 获取记忆列表
        query = query.order_by(Memory.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        memories = result.scalars().all()
        
        return MemoryListResponse(
            memories=[MemoryResponse.model_validate(m) for m in memories],
            total=total
        )
        
    except Exception as e:
        app_logger.error(f"获取记忆列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取记忆列表失败"
        )


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个记忆
    """
    result = await db.execute(
        select(Memory).filter(
            and_(
                Memory.id == memory_id,
                Memory.user_id == current_user.id
            )
        )
    )
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )
    
    return memory


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除记忆
    """
    result = await db.execute(
        select(Memory).filter(
            and_(
                Memory.id == memory_id,
                Memory.user_id == current_user.id
            )
        )
    )
    memory = result.scalar_one_or_none()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )
    
    await db.delete(memory)
    await db.commit()
    
    app_logger.info(f"删除记忆: user_id={current_user.id}, memory_id={memory_id}")
    
    return {"message": "记忆已删除"}


@router.post("/search", response_model=MemoryListResponse)
async def search_memories(
    search_request: MemorySearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索记忆
    """
    try:
        # 使用记忆管理器搜索
        memories = await memory_manager.search_long_term_memory(
            user_id=current_user.id,
            query=search_request.query,
            db=db,
            top_k=search_request.top_k
        )
        
        return MemoryListResponse(
            memories=[MemoryResponse.model_validate(m) for m in memories],
            total=len(memories)
        )
        
    except Exception as e:
        app_logger.error(f"搜索记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索记忆失败"
        )


@router.post("/export")
async def export_memories(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    导出所有记忆数据
    """
    try:
        result = await db.execute(
            select(Memory).filter(Memory.user_id == current_user.id).order_by(Memory.created_at)
        )
        memories = result.scalars().all()
        
        # 格式化导出数据
        export_data = {
            "user_id": current_user.id,
            "username": current_user.username,
            "export_time": datetime.utcnow().isoformat(),
            "total_memories": len(memories),
            "memories": [
                {
                    "id": m.id,
                    "type": m.memory_type.value,
                    "content": m.content,
                    "importance_score": m.importance_score,
                    "created_at": m.created_at.isoformat()
                }
                for m in memories
            ]
        }
        
        app_logger.info(f"导出记忆: user_id={current_user.id}, 数量={len(memories)}")
        
        return export_data
        
    except Exception as e:
        app_logger.error(f"导出记忆失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="导出记忆失败"
        )
