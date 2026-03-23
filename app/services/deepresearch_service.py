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
            status=DeepResearchTaskStatus.DRAFTING_ANALYSTS,
            phase=DeepResearchPhase.ANALYST_GENERATION,
            progress_percent=5,
            progress_message="正在生成分析师草案",
            current_revision=0,
            feedback_round_used=0,
            max_feedback_rounds=task_data.get("max_feedback_rounds", 3),
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

        revision = DeepResearchAnalystRevision(
            task_id=task_id,
            revision_number=expected_revision,
            feedback_text=feedback_text,
            analysts_json=analysts,
            is_selected=False,
        )
        db.add(revision)

        task.current_revision = expected_revision
        task.feedback_round_used = self.calculate_feedback_round_used(expected_revision)
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


deepresearch_service = DeepResearchService()
