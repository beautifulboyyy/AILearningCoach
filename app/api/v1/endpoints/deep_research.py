"""Deep Research API端点"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.research_task import ResearchStatus
from app.schemas.deep_research import (
    StartResearchRequest,
    ResearchTaskResponse,
    HumanFeedbackRequest,
    GenerateAnalystsResponse,
    TaskOperationResponse,
    TaskProgressResponse,
)
from app.ai.deep_research.service import DeepResearchService


router = APIRouter()

def _task_to_response(task) -> ResearchTaskResponse:
    analysts = []
    if getattr(task, "analysts_config", None):
        analysts = (task.analysts_config or {}).get("analysts", [])
    return ResearchTaskResponse(
        id=task.id,
        thread_id=task.thread_id,
        topic=task.topic,
        status=task.status,
        max_analysts=task.max_analysts,
        max_turns=task.max_turns,
        analysts=analysts or None,
        final_report=task.final_report,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("/tasks", response_model=ResearchTaskResponse)
async def start_research(
    request: StartResearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """开始新的研究任务"""
    service = DeepResearchService(db)
    task = await service.create_task(request)

    return _task_to_response(task)


@router.get("/tasks", response_model=List[ResearchTaskResponse])
async def list_research_tasks(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取研究任务列表"""
    service = DeepResearchService(db)
    tasks = await service.list_tasks(limit)
    return [_task_to_response(t) for t in tasks]


@router.get("/tasks/{thread_id}", response_model=ResearchTaskResponse)
async def get_research_task(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取特定研究任务"""
    service = DeepResearchService(db)
    task = await service.get_task_by_thread_id(thread_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return _task_to_response(task)


@router.get("/tasks/{thread_id}/progress", response_model=TaskProgressResponse)
async def get_research_progress(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务运行时进度，不做长期持久化。"""
    service = DeepResearchService(db)
    task = await service.get_task_by_thread_id(thread_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskProgressResponse(**service.get_progress(thread_id))


@router.post("/tasks/{thread_id}/analysts", response_model=GenerateAnalystsResponse)
async def generate_analysts(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """生成分析师并进入人类反馈中断"""
    service = DeepResearchService(db)

    task = await service.get_task_by_thread_id(thread_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    result = await service.generate_analysts(thread_id)
    return GenerateAnalystsResponse(**result)


@router.post("/tasks/{thread_id}/feedback", response_model=TaskOperationResponse)
async def submit_feedback(
    thread_id: str,
    request: HumanFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """提交人类反馈"""
    service = DeepResearchService(db)

    task = await service.get_task_by_thread_id(thread_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    current_status = getattr(task.status, "value", task.status)
    if current_status != ResearchStatus.AWAITING_FEEDBACK.value:
        raise HTTPException(status_code=409, detail="任务当前不处于等待反馈状态")

    feedback = request.feedback if request.action == "regenerate" else None
    result = await service.submit_feedback(thread_id, feedback)
    return TaskOperationResponse(**result)


@router.delete("/tasks/{thread_id}")
async def cancel_research(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除研究任务"""
    service = DeepResearchService(db)
    deleted = await service.delete_task(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {"status": "deleted"}
