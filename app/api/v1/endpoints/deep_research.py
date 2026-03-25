"""Deep Research API端点"""
from typing import List
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.schemas.deep_research import (
    StartResearchRequest, ResearchTaskResponse,
    HumanFeedbackRequest
)
from app.ai.deep_research.service import DeepResearchService


router = APIRouter()


@router.post("/start", response_model=ResearchTaskResponse)
async def start_research(
    request: StartResearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """开始新的研究任务"""
    service = DeepResearchService(db)
    task = await service.create_task(request)

    return ResearchTaskResponse.model_validate(task)


@router.get("", response_model=List[ResearchTaskResponse])
async def list_research_tasks(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取研究任务列表"""
    service = DeepResearchService(db)
    tasks = await service.list_tasks(limit)
    return [ResearchTaskResponse.model_validate(t) for t in tasks]


@router.get("/{thread_id}", response_model=ResearchTaskResponse)
async def get_research_task(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取特定研究任务"""
    service = DeepResearchService(db)
    task = await service.get_task_by_thread_id(thread_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return ResearchTaskResponse.model_validate(task)


@router.post("/{thread_id}/feedback")
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

    result = await service.submit_feedback(thread_id, request.feedback)
    return result


@router.delete("/{thread_id}")
async def cancel_research(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """取消研究任务"""
    service = DeepResearchService(db)

    task = await service.get_task_by_thread_id(thread_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    from app.models.research_task import ResearchStatus
    await service.update_task_status(thread_id, ResearchStatus.CANCELLED)

    return {"status": "cancelled"}


@router.get("/{thread_id}/events")
async def stream_research_events(
    thread_id: str,
    db: AsyncSession = Depends(get_db)
):
    """SSE流式事件"""
    service = DeepResearchService(db)

    task = await service.get_task_by_thread_id(thread_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    async def event_generator():
        async for event in service.run_research(
            thread_id,
            task.topic,
            task.max_analysts
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
