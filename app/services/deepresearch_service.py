"""
DeepResearch 业务服务
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deepresearch import (
    DeepResearchAnalystRevision,
    DeepResearchPhase,
    DeepResearchRun,
    DeepResearchTask,
    DeepResearchTaskStatus,
)
from app.models.user import User
from app.schemas.deepresearch import DeepResearchAnalyst, DeepResearchTaskDetail


class DeepResearchConflictError(Exception):
    """DeepResearch 业务冲突异常"""


class DeepResearchNotFoundError(Exception):
    """DeepResearch 资源不存在异常"""


class DeepResearchService:
    """DeepResearch 业务服务"""

    @staticmethod
    def calculate_feedback_round_used(current_revision: int) -> int:
        """根据当前 revision 计算已用反馈轮次"""
        return max(current_revision - 1, 0)

    @classmethod
    def calculate_remaining_feedback_rounds(
        cls,
        current_revision: int,
        max_feedback_rounds: int,
    ) -> int:
        """计算剩余反馈轮次"""
        used = cls.calculate_feedback_round_used(current_revision=current_revision)
        return max(max_feedback_rounds - used, 0)

    @classmethod
    def ensure_feedback_allowed(
        cls,
        current_revision: int,
        max_feedback_rounds: int,
    ) -> None:
        """校验当前是否仍允许提交反馈"""
        remaining = cls.calculate_remaining_feedback_rounds(
            current_revision=current_revision,
            max_feedback_rounds=max_feedback_rounds,
        )
        if remaining <= 0:
            raise DeepResearchConflictError("反馈轮次已用尽")

    async def _lock_user(self, user_id: int, db: AsyncSession) -> User:
        """在事务中锁定用户记录，避免并发创建穿透限制。"""
        bind = db.get_bind()
        stmt = select(User).where(User.id == user_id)
        if bind is not None and bind.dialect.name != "sqlite":
            stmt = stmt.with_for_update()

        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise DeepResearchNotFoundError("用户不存在")
        return user

    async def create_task(
        self,
        user_id: int,
        task_data: dict[str, Any],
        db: AsyncSession,
    ) -> DeepResearchTask:
        """创建 DeepResearch 任务并进入 analyst drafting 状态。"""
        await self._lock_user(user_id=user_id, db=db)

        running_result = await db.execute(
            select(DeepResearchTask).where(
                DeepResearchTask.user_id == user_id,
                DeepResearchTask.status.in_(
                    [
                        DeepResearchTaskStatus.DRAFTING_ANALYSTS,
                        DeepResearchTaskStatus.RUNNING_RESEARCH,
                    ]
                ),
            )
        )
        running_task = running_result.scalar_one_or_none()
        if running_task is not None:
            raise DeepResearchConflictError("当前已有运行中的 DeepResearch 任务")

        task = DeepResearchTask(
            user_id=user_id,
            topic=task_data["topic"],
            requirements=task_data.get("requirements"),
            max_analysts=task_data.get("max_analysts", 4),
            status=DeepResearchTaskStatus.DRAFTING_ANALYSTS,
            phase=DeepResearchPhase.ANALYST_GENERATION,
            progress_percent=5,
            progress_message="正在生成分析师草案",
            current_revision=0,
            feedback_round_used=0,
            max_feedback_rounds=task_data.get("max_feedback_rounds", 3),
            pending_feedback_text=None,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    async def get_task(
        self,
        task_id: int,
        user_id: int,
        db: AsyncSession,
    ) -> Optional[DeepResearchTask]:
        result = await db.execute(
            select(DeepResearchTask).where(
                DeepResearchTask.id == task_id,
                DeepResearchTask.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_task_for_execution(
        self,
        task_id: int,
        db: AsyncSession,
        expected_status: str | None = None,
    ) -> Optional[DeepResearchTask]:
        """为异步任务读取任务，并可选校验预期状态。"""
        result = await db.execute(select(DeepResearchTask).where(DeepResearchTask.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            return None
        if expected_status is not None and task.status.value != expected_status:
            return None
        return task

    async def finalize_analyst_revision(
        self,
        task_id: int,
        expected_revision: int,
        analysts: list[dict[str, Any]],
        feedback_text: Optional[str],
        db: AsyncSession,
    ) -> DeepResearchTask:
        """写入 analyst revision 并推进到 waiting_feedback。"""
        result = await db.execute(select(DeepResearchTask).where(DeepResearchTask.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            raise DeepResearchNotFoundError("DeepResearch 任务不存在")
        if task.status != DeepResearchTaskStatus.DRAFTING_ANALYSTS:
            raise DeepResearchConflictError("当前任务状态不允许写入分析师版本")
        if task.current_revision + 1 != expected_revision:
            raise DeepResearchConflictError("分析师版本号不匹配")

        persisted_feedback = feedback_text if feedback_text is not None else task.pending_feedback_text
        revision = DeepResearchAnalystRevision(
            task_id=task_id,
            revision_number=expected_revision,
            feedback_text=persisted_feedback,
            analysts_json=analysts,
            is_selected=False,
        )
        db.add(revision)

        task.current_revision = expected_revision
        task.feedback_round_used = self.calculate_feedback_round_used(expected_revision)
        task.pending_feedback_text = None
        task.status = DeepResearchTaskStatus.WAITING_FEEDBACK
        task.phase = DeepResearchPhase.ANALYST_FEEDBACK
        task.progress_percent = 25
        task.progress_message = "已生成分析师草案，等待反馈"

        await db.commit()
        await db.refresh(task)
        return task

    async def submit_feedback(
        self,
        task_id: int,
        user_id: int,
        feedback: str,
        db: AsyncSession,
    ) -> DeepResearchTask:
        """提交反馈并将任务重新切回 analyst drafting。"""
        task = await self.get_task(task_id=task_id, user_id=user_id, db=db)
        if task is None:
            raise DeepResearchNotFoundError("DeepResearch 任务不存在")
        if task.status != DeepResearchTaskStatus.WAITING_FEEDBACK:
            raise DeepResearchConflictError("当前任务状态不允许提交反馈")

        self.ensure_feedback_allowed(
            current_revision=task.current_revision,
            max_feedback_rounds=task.max_feedback_rounds,
        )

        task.pending_feedback_text = feedback
        task.status = DeepResearchTaskStatus.DRAFTING_ANALYSTS
        task.phase = DeepResearchPhase.ANALYST_GENERATION
        task.progress_percent = 10
        task.progress_message = "正在根据反馈重新生成分析师草案"
        await db.commit()
        await db.refresh(task)
        return task

    async def start_research(
        self,
        task_id: int,
        user_id: int,
        selected_revision: int,
        db: AsyncSession,
    ) -> DeepResearchTask:
        """锁定 analyst revision 并进入正式研究。"""
        task = await self.get_task(task_id=task_id, user_id=user_id, db=db)
        if task is None:
            raise DeepResearchNotFoundError("DeepResearch 任务不存在")
        if task.status != DeepResearchTaskStatus.WAITING_FEEDBACK:
            raise DeepResearchConflictError("当前任务状态不允许启动研究")

        revision_result = await db.execute(
            select(DeepResearchAnalystRevision).where(
                DeepResearchAnalystRevision.task_id == task_id,
                DeepResearchAnalystRevision.revision_number == selected_revision,
            )
        )
        revision = revision_result.scalar_one_or_none()
        if revision is None:
            raise DeepResearchConflictError("指定 revision 不存在")

        await db.execute(
            update(DeepResearchAnalystRevision)
            .where(DeepResearchAnalystRevision.task_id == task_id)
            .values(is_selected=False)
        )
        await db.execute(
            update(DeepResearchAnalystRevision)
            .where(
                DeepResearchAnalystRevision.task_id == task_id,
                DeepResearchAnalystRevision.revision_number == selected_revision,
            )
            .values(is_selected=True)
        )

        task.selected_revision = selected_revision
        task.status = DeepResearchTaskStatus.RUNNING_RESEARCH
        task.phase = DeepResearchPhase.RESEARCH_EXECUTION
        task.progress_percent = 30
        task.progress_message = "正在执行正式研究"

        run = DeepResearchRun(
            task_id=task_id,
            revision_number=selected_revision,
            status="running",
            progress_percent=0,
            progress_message="研究任务已启动",
        )
        db.add(run)

        await db.commit()
        await db.refresh(task)
        return task

    async def list_tasks(
        self,
        user_id: int,
        db: AsyncSession,
    ) -> list[DeepResearchTask]:
        result = await db.execute(
            select(DeepResearchTask)
            .where(DeepResearchTask.user_id == user_id)
            .order_by(DeepResearchTask.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_task_detail(
        self,
        task_id: int,
        user_id: int,
        db: AsyncSession,
    ) -> DeepResearchTaskDetail:
        """获取任务详情。"""
        task = await self.get_task(task_id=task_id, user_id=user_id, db=db)
        if task is None:
            raise DeepResearchNotFoundError("DeepResearch 任务不存在")

        revision_number = task.selected_revision or task.current_revision
        analysts: list[DeepResearchAnalyst] = []
        if revision_number:
            result = await db.execute(
                select(DeepResearchAnalystRevision).where(
                    DeepResearchAnalystRevision.task_id == task_id,
                    DeepResearchAnalystRevision.revision_number == revision_number,
                )
            )
            revision = result.scalar_one_or_none()
            if revision and revision.analysts_json:
                analysts = [DeepResearchAnalyst.model_validate(item) for item in revision.analysts_json]

        return DeepResearchTaskDetail(
            id=task.id,
            user_id=task.user_id,
            topic=task.topic,
            requirements=task.requirements,
            status=task.status,
            phase=task.phase,
            progress_percent=task.progress_percent,
            progress_message=task.progress_message,
            current_revision=task.current_revision,
            feedback_round_used=task.feedback_round_used,
            max_feedback_rounds=task.max_feedback_rounds,
            selected_revision=task.selected_revision,
            created_at=task.created_at,
            updated_at=task.updated_at,
            remaining_feedback_rounds=self.calculate_remaining_feedback_rounds(
                current_revision=task.current_revision,
                max_feedback_rounds=task.max_feedback_rounds,
            ),
            analysts=analysts,
            report_available=bool(task.final_report_markdown),
            error_message=task.error_message,
        )

    async def get_selected_analysts(
        self,
        task_id: int,
        selected_revision: int,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """读取被锁定 revision 的分析师列表。"""
        result = await db.execute(
            select(DeepResearchAnalystRevision).where(
                DeepResearchAnalystRevision.task_id == task_id,
                DeepResearchAnalystRevision.revision_number == selected_revision,
            )
        )
        revision = result.scalar_one_or_none()
        if revision is None:
            raise DeepResearchConflictError("选定的分析师版本不存在")
        return revision.analysts_json or []

    async def get_feedback_history(
        self,
        task_id: int,
        db: AsyncSession,
    ) -> list[str]:
        """按时间顺序读取历史反馈，并附加当前待消费反馈。"""
        result = await db.execute(
            select(DeepResearchAnalystRevision)
            .where(DeepResearchAnalystRevision.task_id == task_id)
            .order_by(DeepResearchAnalystRevision.revision_number)
        )
        revisions = result.scalars().all()
        feedback_history = [item.feedback_text for item in revisions if item.feedback_text]

        task_result = await db.execute(select(DeepResearchTask).where(DeepResearchTask.id == task_id))
        task = task_result.scalar_one_or_none()
        if task is not None and task.pending_feedback_text:
            feedback_history.append(task.pending_feedback_text)
        return feedback_history

    async def finalize_research_run(
        self,
        task_id: int,
        selected_revision: int,
        final_report: str,
        sources: list[dict[str, Any]],
        db: AsyncSession,
    ) -> Optional[dict[str, Any]]:
        """写回正式研究结果。"""
        task = await self.get_task_for_execution(
            task_id=task_id,
            db=db,
            expected_status=DeepResearchTaskStatus.RUNNING_RESEARCH.value,
        )
        if task is None or task.selected_revision != selected_revision:
            return None

        result = await db.execute(
            select(DeepResearchRun).where(
                DeepResearchRun.task_id == task_id,
                DeepResearchRun.revision_number == selected_revision,
            )
        )
        run = result.scalar_one_or_none()
        if run is None:
            run = DeepResearchRun(
                task_id=task_id,
                revision_number=selected_revision,
            )
            db.add(run)

        run.status = "completed"
        run.progress_percent = 100
        run.progress_message = "报告已生成"
        run.result_json = {"sources": sources}
        task.status = DeepResearchTaskStatus.COMPLETED
        task.phase = DeepResearchPhase.REPORT_FINALIZATION
        task.progress_percent = 100
        task.progress_message = "报告已生成"
        task.final_report_markdown = final_report

        await db.commit()
        await db.refresh(task)
        return {"status": "completed", "task_id": task_id}

    async def mark_task_failed(
        self,
        task_id: int,
        message: str,
        db: AsyncSession,
        expected_status: str | None = None,
        selected_revision: int | None = None,
    ) -> None:
        """标记任务失败。"""
        task = await self.get_task_for_execution(
            task_id=task_id,
            db=db,
            expected_status=expected_status,
        )
        if task is None:
            return
        if selected_revision is not None and task.selected_revision != selected_revision:
            return
        task.status = DeepResearchTaskStatus.FAILED
        task.error_message = message
        task.progress_message = "任务执行失败"

        run = None
        if selected_revision is not None:
            result = await db.execute(
                select(DeepResearchRun).where(
                    DeepResearchRun.task_id == task_id,
                    DeepResearchRun.revision_number == selected_revision,
                )
            )
            run = result.scalar_one_or_none()
        else:
            result = await db.execute(
                select(DeepResearchRun)
                .where(DeepResearchRun.task_id == task_id)
                .order_by(DeepResearchRun.created_at.desc())
            )
            run = result.scalars().first()
        if run is not None:
            run.status = "failed"
            run.error_message = message

        await db.commit()

    async def get_report(
        self,
        task_id: int,
        user_id: int,
        db: AsyncSession,
    ) -> str:
        """获取最终报告。"""
        task = await self.get_task(task_id=task_id, user_id=user_id, db=db)
        if task is None:
            raise DeepResearchNotFoundError("DeepResearch 任务不存在")
        if not task.final_report_markdown:
            raise DeepResearchConflictError("研究尚未完成，暂无报告")
        return task.final_report_markdown

    async def delete_task(
        self,
        task_id: int,
        user_id: int,
        db: AsyncSession,
    ) -> None:
        """删除任务及其关联版本、运行记录。"""
        task = await self.get_task(task_id=task_id, user_id=user_id, db=db)
        if task is None:
            raise DeepResearchNotFoundError("DeepResearch 任务不存在")

        await db.delete(task)
        await db.commit()


deepresearch_service = DeepResearchService()
