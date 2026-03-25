"""Deep Research 服务层"""
import uuid
import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.research_task import ResearchTask, ResearchStatus
from app.schemas.deep_research import StartResearchRequest
from app.ai.deep_research.graph_builder import research_graph
from app.ai.deep_research.config import get_config


class DeepResearchService:
    """Deep Research 服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.config = get_config()

    async def create_task(self, request: StartResearchRequest) -> ResearchTask:
        """创建新研究任务"""
        thread_id = f"research_{uuid.uuid4().hex[:12]}"

        task = ResearchTask(
            thread_id=thread_id,
            topic=request.topic,
            status=ResearchStatus.PENDING,
            max_analysts=request.max_analysts,
            max_turns=self.config.max_turns,
            analysts_config={"directions": request.analyst_directions}
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def get_task_by_thread_id(self, thread_id: str) -> Optional[ResearchTask]:
        """通过thread_id获取任务"""
        result = await self.db.execute(
            select(ResearchTask).where(ResearchTask.thread_id == thread_id)
        )
        return result.scalar_one_or_none()

    async def list_tasks(self, limit: int = 50) -> list[ResearchTask]:
        """获取任务列表"""
        result = await self.db.execute(
            select(ResearchTask)
            .order_by(ResearchTask.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_task_status(self, thread_id: str, status: ResearchStatus, final_report: str = None):
        """更新任务状态"""
        task = await self.get_task_by_thread_id(thread_id)
        if task:
            task.status = status
            if final_report:
                task.final_report = final_report
            await self.db.commit()

    async def submit_feedback(self, thread_id: str, feedback: Optional[str]) -> Dict[str, Any]:
        """提交人类反馈并继续执行"""
        config = {"configurable": {"thread_id": thread_id}}

        if feedback:
            research_graph.update_state(
                config,
                {"human_analyst_feedback": feedback},
                as_node="human_feedback"
            )
        else:
            research_graph.update_state(
                config,
                {"human_analyst_feedback": None},
                as_node="human_feedback"
            )

        task = await self.get_task_by_thread_id(thread_id)
        if task:
            await self.update_task_status(thread_id, ResearchStatus.RUNNING)

        return {"status": "continued"}

    async def run_research(self, thread_id: str, topic: str, max_analysts: int) -> AsyncGenerator[Dict[str, Any], None]:
        """运行研究工作流"""
        config = {"configurable": {"thread_id": thread_id}}

        await self.update_task_status(thread_id, ResearchStatus.RUNNING)

        initial_state = {
            "topic": topic,
            "max_analysts": max_analysts,
            "human_analyst_feedback": "",
        }

        try:
            async for event in research_graph.astream_events(
                initial_state,
                config,
                stream_mode="values"
            ):
                event_type = self._classify_event(event)
                if event_type:
                    yield event_type

        except Exception as e:
            await self.update_task_status(thread_id, ResearchStatus.FAILED)
            yield {"type": "error", "data": {"message": str(e)}}

        final_state = research_graph.get_state(config)
        final_report = final_state.values.get("final_report", "")

        await self.update_task_status(
            thread_id,
            ResearchStatus.COMPLETED,
            final_report=final_report
        )

        yield {"type": "done", "data": {"final_report": final_report}}

    def _classify_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分类事件类型"""
        if "create_analysts" in event:
            return {"type": "status", "data": {"message": "正在生成分析师..."}}
        return None
