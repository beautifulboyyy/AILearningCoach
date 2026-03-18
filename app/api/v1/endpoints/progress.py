"""
学习进度相关API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.progress import ProgressStatus, ProgressTriggerType
from app.schemas.progress import (
    ProgressResponse,
    ProgressUpdate,
    ProgressStatsResponse,
    WeeklyReportResponse,
    ModuleProgressUpdateRequest,
    RecordActivityRequest,
    RecordActivityResponse
)
from app.schemas.learning_path import PathProgressResponse
from app.services.progress_service import progress_service
from app.services.progress_sync_service import progress_sync_service
from app.services.learning_path_service import learning_path_service
from app.utils.logger import app_logger

router = APIRouter()


@router.get("/stats", response_model=ProgressStatsResponse)
async def get_progress_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取学习进度统计
    """
    try:
        stats = await progress_service.get_progress_stats(
            user_id=current_user.id,
            db=db
        )
        return ProgressStatsResponse(**stats)
        
    except Exception as e:
        app_logger.error(f"获取进度统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取进度统计失败"
        )


@router.put("/{module_name}", response_model=ProgressResponse)
async def update_progress(
    module_name: str,
    update_data: ProgressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新模块学习进度
    """
    try:
        progress = await progress_service.update_progress(
            user_id=current_user.id,
            module_name=module_name,
            status=update_data.status or ProgressStatus.IN_PROGRESS,
            completion_percentage=update_data.completion_percentage or 0.0,
            db=db
        )
        
        return progress
        
    except Exception as e:
        app_logger.error(f"更新进度失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新进度失败"
        )


@router.put("/module/{module_key}")
async def update_module_progress_by_key(
    module_key: str,
    update_data: ModuleProgressUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    按模块key更新进度（学习路径模块专用）
    """
    try:
        # 先拿当前路径进度（用于计算delta）
        path = await learning_path_service.get_active_learning_path(
            user_id=current_user.id,
            db=db
        )
        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="暂无活跃学习路径"
            )

        current_progress_data = await progress_sync_service.get_path_progress(
            path_id=path.id,
            user_id=current_user.id,
            db=db
        )

        current_percentage = 0.0
        if current_progress_data:
            for phase in current_progress_data.get("phases", []):
                for module in phase.get("modules", []):
                    if module.get("module_key") == module_key:
                        current_percentage = float(module.get("completion_percentage", 0.0))
                        break

        target_percentage = update_data.completion_percentage
        target_status = update_data.status
        delta = 0.0

        if target_percentage is not None:
            delta = float(target_percentage) - current_percentage
        elif target_status == ProgressStatus.COMPLETED:
            delta = 100.0 - current_percentage
        elif target_status == ProgressStatus.IN_PROGRESS:
            # 至少推进到1%，避免状态为in_progress但进度仍为0
            delta = max(1.0 - current_percentage, 0.0)
        elif target_status == ProgressStatus.NOT_STARTED:
            delta = -current_percentage

        progress = await progress_sync_service.update_module_progress(
            user_id=current_user.id,
            module_key=module_key,
            completion_delta=delta,
            trigger_type=ProgressTriggerType.MANUAL,
            trigger_source=f"api:module_update:{module_key}",
            trigger_detail=update_data.notes or "manual update",
            db=db
        )

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到该模块，请确认模块标识正确"
            )

        return {
            "module_key": module_key,
            "old_progress": round(current_percentage, 2),
            "new_progress": round(progress.completion_percentage, 2),
            "progress_change": round(delta, 2),
            "message": "模块进度更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"按模块key更新进度失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新模块进度失败"
        )


@router.get("/report/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取周报
    """
    try:
        report = await progress_service.generate_weekly_report(
            user_id=current_user.id,
            db=db
        )
        return WeeklyReportResponse(**report)

    except Exception as e:
        app_logger.error(f"生成周报失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成周报失败"
        )


@router.post("/sync")
async def sync_path_modules(
    path_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    同步学习路径模块到进度表

    如果不指定 path_id，则同步用户当前活跃的学习路径
    """
    try:
        # 获取学习路径
        if path_id:
            path = await learning_path_service.get_learning_path(
                path_id=path_id,
                user_id=current_user.id,
                db=db
            )
        else:
            path = await learning_path_service.get_active_learning_path(
                user_id=current_user.id,
                db=db
            )

        if not path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学习路径不存在"
            )

        # 同步模块
        modules = await progress_sync_service.sync_path_modules(path, db)

        return {
            "message": "同步成功",
            "path_id": path.id,
            "synced_modules": len(modules)
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"同步路径模块失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="同步路径模块失败"
        )


@router.get("/path/{path_id}", response_model=PathProgressResponse)
async def get_path_progress(
    path_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取学习路径的详细进度

    返回按阶段组织的模块进度详情
    """
    try:
        progress_data = await progress_sync_service.get_path_progress(
            path_id=path_id,
            user_id=current_user.id,
            db=db
        )

        if not progress_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学习路径不存在"
            )

        return PathProgressResponse(**progress_data)

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"获取路径进度失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取路径进度失败"
        )


@router.get("/history")
async def get_progress_history(
    module_key: Optional[str] = Query(None, description="过滤特定模块"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取进度变更历史

    记录所有进度变更的详细历史，包括触发来源
    """
    try:
        history = await progress_sync_service.get_progress_history(
            user_id=current_user.id,
            module_key=module_key,
            limit=limit,
            db=db
        )

        return {
            "items": history,
            "total": len(history)
        }

    except Exception as e:
        app_logger.error(f"获取进度历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取进度历史失败"
        )


@router.post("/module/{module_key}/activity", response_model=RecordActivityResponse)
async def record_learning_activity(
    module_key: str,
    activity: RecordActivityRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    记录学习活动并更新进度

    根据活动类型和时长自动计算进度增量：
    - study: 每30分钟 +5%
    - practice: 每30分钟 +10%
    - review: 每30分钟 +3%
    """
    try:
        # 根据活动类型计算进度增量
        activity_multipliers = {
            "study": 5.0,      # 学习：每30分钟 +5%
            "practice": 10.0,  # 练习：每30分钟 +10%
            "review": 3.0      # 复习：每30分钟 +3%
        }

        multiplier = activity_multipliers.get(activity.activity_type, 5.0)
        progress_delta = (activity.duration_minutes / 30) * multiplier

        # 更新进度
        progress = await progress_sync_service.update_module_progress(
            user_id=current_user.id,
            module_key=module_key,
            completion_delta=progress_delta,
            trigger_type=ProgressTriggerType.TIME_BASED,
            trigger_source=f"activity:{activity.activity_type}",
            trigger_detail=f"{activity.duration_minutes}分钟{activity.activity_type}",
            db=db
        )

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到该模块，请确认模块标识正确且已创建学习路径"
            )

        old_progress = progress.completion_percentage - progress_delta

        return RecordActivityResponse(
            module_key=module_key,
            old_progress=round(max(0, old_progress), 2),
            new_progress=round(progress.completion_percentage, 2),
            progress_change=round(progress_delta, 2),
            message=f"已记录{activity.duration_minutes}分钟的{activity.activity_type}活动，进度+{progress_delta:.1f}%"
        )

    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"记录学习活动失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="记录学习活动失败"
        )
