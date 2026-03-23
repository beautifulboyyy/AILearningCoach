"""
DeepResearch Celery 任务
"""
from celery_app import celery_app
from app.db.session import async_session_maker
from app.services.deepresearch_runner import deepresearch_runner
from app.services.deepresearch_service import deepresearch_service
from app.utils.logger import app_logger
import asyncio


def run_async(coro):
    """运行异步函数的辅助函数"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


async def _generate_analysts_task(task_id: int, expected_revision: int, expected_status: str):
    async with async_session_maker() as db:
        task = await deepresearch_service.get_task_for_execution(
            task_id=task_id,
            db=db,
            expected_status=expected_status,
        )
        if task is None:
            app_logger.info(f"stale analyst task skipped: task_id={task_id}, revision={expected_revision}")
            return {"status": "stale", "task_id": task_id}

        try:
            feedback_history = await deepresearch_service.get_feedback_history(task_id=task_id, db=db)
            analysts = await deepresearch_runner.generate_analysts(
                topic=task.topic,
                requirements=task.requirements,
                max_analysts=task.max_analysts,
                feedback_history=feedback_history,
            )
            finalized = await deepresearch_service.finalize_analyst_revision(
                task_id=task_id,
                expected_revision=expected_revision,
                analysts=[item.model_dump() if hasattr(item, "model_dump") else item for item in analysts],
                feedback_text=task.pending_feedback_text,
                db=db,
            )
            if finalized is None:
                app_logger.info(f"stale analyst task write skipped: task_id={task_id}, revision={expected_revision}")
                return {"status": "stale", "task_id": task_id}
            return {"status": "completed", "task_id": task_id, "revision": expected_revision}
        except Exception as exc:
            await deepresearch_service.mark_task_failed(
                task_id=task_id,
                message=str(exc),
                db=db,
                expected_status=expected_status,
            )
            return {"status": "failed", "task_id": task_id}


async def _run_deepresearch_task(task_id: int, selected_revision: int, expected_status: str):
    async with async_session_maker() as db:
        task = await deepresearch_service.get_task_for_execution(
            task_id=task_id,
            db=db,
            expected_status=expected_status,
        )
        if task is None or task.selected_revision != selected_revision:
            app_logger.info(f"stale research task skipped: task_id={task_id}, revision={selected_revision}")
            return {"status": "stale", "task_id": task_id}

        try:
            analysts = await deepresearch_service.get_selected_analysts(
                task_id=task_id,
                selected_revision=selected_revision,
                db=db,
            )
            result = await deepresearch_runner.run_research(
                topic=task.topic,
                selected_analysts=analysts,
            )
            finalized = await deepresearch_service.finalize_research_run(
                task_id=task_id,
                selected_revision=selected_revision,
                final_report=result["final_report"],
                sources=result.get("sources", []),
                db=db,
            )
            if finalized is None:
                return {"status": "stale", "task_id": task_id}
            return finalized
        except Exception as exc:
            await deepresearch_service.mark_task_failed(
                task_id=task_id,
                message=str(exc),
                db=db,
                expected_status=expected_status,
                selected_revision=selected_revision,
            )
            return {"status": "failed", "task_id": task_id}


@celery_app.task(name="app.tasks.deepresearch_tasks.generate_analysts_task")
def generate_analysts_task(task_id: int, expected_revision: int, expected_status: str = "drafting_analysts"):
    return run_async(
        _generate_analysts_task(
            task_id=task_id,
            expected_revision=expected_revision,
            expected_status=expected_status,
        )
    )


@celery_app.task(name="app.tasks.deepresearch_tasks.run_deepresearch_task")
def run_deepresearch_task(task_id: int, selected_revision: int, expected_status: str = "running_research"):
    return run_async(
        _run_deepresearch_task(
            task_id=task_id,
            selected_revision=selected_revision,
            expected_status=expected_status,
        )
    )
