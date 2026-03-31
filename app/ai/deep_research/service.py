"""Deep Research 服务层"""
import uuid
import asyncio
from copy import deepcopy
import json
from typing import AsyncGenerator, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.types import Command

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
            analysts_config={
                "directions": request.analyst_directions or [],
                "analysts": [],
            }
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

    def _extract_analysts(self, task: ResearchTask) -> list[dict]:
        """从任务配置中提取分析师快照"""
        config = task.analysts_config or {}
        return config.get("analysts", [])

    def _store_analysts(self, task: ResearchTask, analysts: list[dict]):
        """将最新分析师快照写回任务配置"""
        config = deepcopy(task.analysts_config or {})
        config["analysts"] = analysts
        task.analysts_config = config

    async def _handle_graph_result(self, thread_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """统一处理图执行结果"""
        if not result:
            await self.update_task_status(thread_id, ResearchStatus.FAILED)
            return {
                "status": "failed",
                "thread_id": thread_id,
                "message": "研究图未返回结果",
                "error": "Graph returned None",
                "final_report": "",
                "sections_count": 0,
            }

        if "__interrupt__" in result:
            state = research_graph.get_state({"configurable": {"thread_id": thread_id}})
            analysts = state.values.get("analysts", [])
            task = await self.get_task_by_thread_id(thread_id)
            if task:
                self._store_analysts(task, analysts)
                await self.update_task_status(thread_id, ResearchStatus.AWAITING_FEEDBACK)
            return {
                "status": "awaiting_feedback",
                "thread_id": thread_id,
                "message": "请确认分析师或提供新的自然语言要求",
                "analysts": analysts,
                "final_report": "",
                "sections_count": 0,
                "error": "",
            }

        final_report = result.get("final_report", "")
        sections_count = len(result.get("sections", []))

        if not final_report.strip():
            await self.update_task_status(thread_id, ResearchStatus.FAILED)
            return {
                "status": "failed",
                "thread_id": thread_id,
                "message": "研究图未生成有效报告",
                "error": "Graph returned empty final_report",
                "final_report": "",
                "sections_count": sections_count,
            }

        await self.update_task_status(
            thread_id,
            ResearchStatus.COMPLETED,
            final_report=final_report,
        )
        return {
            "status": "completed",
            "thread_id": thread_id,
            "message": "研究完成",
            "final_report": final_report,
            "sections_count": sections_count,
            "error": "",
        }

    async def generate_analysts(self, thread_id: str) -> Dict[str, Any]:
        """生成分析师并在确认节点中断"""
        task = await self.get_task_by_thread_id(thread_id)
        if not task:
            raise ValueError("任务不存在")

        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {
            "topic": task.topic,
            "max_analysts": task.max_analysts,
            "human_analyst_feedback": "",
        }

        result = research_graph.invoke(initial_state, config)
        handled = await self._handle_graph_result(thread_id, result)
        return {
            "status": handled["status"],
            "thread_id": thread_id,
            "analysts": handled.get("analysts", []),
            "interrupt_required": handled["status"] == "awaiting_feedback",
        }

    async def submit_feedback(self, thread_id: str, feedback: Optional[str]) -> Dict[str, Any]:
        """提交人类反馈并继续执行或重新生成分析师"""
        config = {"configurable": {"thread_id": thread_id}}
        task = await self.get_task_by_thread_id(thread_id)
        if not task:
            raise ValueError("任务不存在")

        if feedback:
            result = research_graph.invoke(
                Command(resume={"action": "regenerate", "feedback": feedback}),
                config,
            )
            handled = await self._handle_graph_result(thread_id, result)
            return {
                "status": handled["status"],
                "thread_id": thread_id,
                "message": "已根据反馈重新生成分析师",
                "analysts": handled.get("analysts", []),
                "final_report": "",
                "sections_count": 0,
                "error": "",
            }

        await self.update_task_status(thread_id, ResearchStatus.RUNNING)
        result = research_graph.invoke(
            Command(resume={"action": "approve"}),
            config,
        )
        handled = await self._handle_graph_result(thread_id, result)
        return handled

    async def run_research_sync(self, thread_id: str, topic: str, max_analysts: int) -> Dict[str, Any]:
        """同步运行研究工作流，直接返回完整结果（无流式输出）"""
        config = {"configurable": {"thread_id": thread_id}}

        await self.update_task_status(thread_id, ResearchStatus.RUNNING)

        initial_state = {
            "topic": topic,
            "max_analysts": max_analysts,
            "human_analyst_feedback": "",
        }

        def _invoke_graph():
            """在同步线程中执行 graph.invoke()"""
            result = research_graph.invoke(initial_state, config)
            return result

        try:
            # 在线程池中执行同步的 graph.invoke()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _invoke_graph)
            return await self._handle_graph_result(thread_id, result)

        except Exception as e:
            await self.update_task_status(thread_id, ResearchStatus.FAILED)
            return {
                "status": "failed",
                "thread_id": thread_id,
                "message": "研究执行失败",
                "error": str(e),
                "final_report": "",
                "sections_count": 0,
            }

    async def run_research(self, thread_id: str, topic: str, max_analysts: int) -> AsyncGenerator[Dict[str, Any], None]:
        """运行研究工作流（SSE流式版本，已废弃，请使用 run_research_sync）"""
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
        event_name = event.get("name") or ""
        event_type = event.get("event") or ""

        output = event.get("data", {}).get("output")
        if output is not None and "final_report" in output:
            return None  # 忽略最终输出事件

        if "create_analysts" in event_name:
            return {"type": "status", "data": {"message": "正在生成分析师..."}}
        if event_name == "conduct_interview":
            return {"type": "status", "data": {"message": "正在访谈分析师..."}}
        if event_name == "write_report":
            return {"type": "status", "data": {"message": "正在撰写报告..."}}

        # 通用状态事件
        if event_type == "on_chain_start":
            return {"type": "status", "data": {"message": f"执行节点: {event_name}"}}

        return None
