"""
DeepResearch 相关 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.deepresearch import (
    DeepResearchFeedbackCreate,
    DeepResearchReportResponse,
    DeepResearchStartRequest,
    DeepResearchTaskCreate,
    DeepResearchTaskDetail,
    DeepResearchTaskListResponse,
    DeepResearchTaskSummary,
)
from app.services.deepresearch_service import (
    DeepResearchConflictError,
    DeepResearchNotFoundError,
    deepresearch_service,
)
from app.tasks.deepresearch_tasks import generate_analysts_task, run_deepresearch_task

router = APIRouter()


@router.post("/tasks", response_model=DeepResearchTaskSummary, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: DeepResearchTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        task = await deepresearch_service.create_task(
            user_id=current_user.id,
            task_data=request.model_dump(),
            db=db,
        )
        generate_analysts_task.delay(
            task_id=task.id,
            expected_revision=1,
            expected_status="drafting_analysts",
        )
        return DeepResearchTaskSummary.model_validate(task)
    except DeepResearchConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/tasks", response_model=DeepResearchTaskListResponse)
async def list_tasks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    tasks = await deepresearch_service.list_tasks(user_id=current_user.id, db=db)
    return DeepResearchTaskListResponse(
        tasks=[DeepResearchTaskSummary.model_validate(task) for task in tasks],
        total=len(tasks),
    )


@router.get("/tasks/{task_id}", response_model=DeepResearchTaskDetail)
async def get_task_detail(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await deepresearch_service.get_task_detail(
            task_id=task_id,
            user_id=current_user.id,
            db=db,
        )
    except DeepResearchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/feedback", response_model=DeepResearchTaskSummary)
async def submit_feedback(
    task_id: int,
    request: DeepResearchFeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        task = await deepresearch_service.submit_feedback(
            task_id=task_id,
            user_id=current_user.id,
            feedback=request.feedback,
            db=db,
        )
        generate_analysts_task.delay(
            task_id=task.id,
            expected_revision=task.current_revision + 1,
            expected_status="drafting_analysts",
        )
        return DeepResearchTaskSummary.model_validate(task)
    except DeepResearchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DeepResearchConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/start", response_model=DeepResearchTaskSummary)
async def start_research(
    task_id: int,
    request: DeepResearchStartRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        task = await deepresearch_service.start_research(
            task_id=task_id,
            user_id=current_user.id,
            selected_revision=request.selected_revision,
            db=db,
        )
        run_deepresearch_task.delay(
            task_id=task.id,
            selected_revision=request.selected_revision,
            expected_status="running_research",
        )
        return DeepResearchTaskSummary.model_validate(task)
    except DeepResearchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DeepResearchConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/tasks/{task_id}/report", response_model=DeepResearchReportResponse)
async def get_report(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        report = await deepresearch_service.get_report(
            task_id=task_id,
            user_id=current_user.id,
            db=db,
        )
        task = await deepresearch_service.get_task(task_id=task_id, user_id=current_user.id, db=db)
        return DeepResearchReportResponse(
            task_id=task_id,
            topic=task.topic if task else "",
            report_markdown=report,
        )
    except DeepResearchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DeepResearchConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
