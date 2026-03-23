"""
DeepResearch Runner
"""
import json
import re
from typing import Any, List

from app.ai.deepresearch.models import DeepResearchAnalystProfile
from app.ai.deepresearch.prompts import ANALYST_SYSTEM_PROMPT, REPORT_SYSTEM_PROMPT
from app.ai.deepresearch.search import DeepResearchSearchAdapter
from app.ai.rag.llm import llm


class DeepResearchRunner:
    """DeepResearch AI 调度入口"""

    def __init__(self, llm_client: Any = None, search_service: Any = None):
        self.llm_client = llm_client or llm
        self.search_service = search_service or DeepResearchSearchAdapter.from_settings()

    async def search(self, query: str) -> List[dict]:
        return await self.search_service.search(query)

    @staticmethod
    def _extract_json_payload(content: str) -> Any:
        """从模型返回中提取 JSON，兼容 fenced code block 和前后说明文字。"""
        text = content.strip()

        fenced_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fenced_match:
            text = fenced_match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start_positions = [idx for idx in (text.find("["), text.find("{")) if idx != -1]
            if not start_positions:
                raise

            start = min(start_positions)
            for end in range(len(text), start, -1):
                candidate = text[start:end].strip()
                if not candidate:
                    continue
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
            raise

    async def generate_analysts(
        self,
        topic: str,
        requirements: str | None,
        max_analysts: int,
        feedback_history: list[str],
    ) -> list[DeepResearchAnalystProfile]:
        user_message = (
            f"请基于主题生成分析师。\n"
            f"主题：{topic}\n"
            f"补充要求：{requirements or '无'}\n"
            f"最大分析师数量：{max_analysts}\n"
            f"历史反馈：{feedback_history or []}\n"
            f"生成分析师"
        )
        content = await self.llm_client.chat(
            user_message=user_message,
            system_message=ANALYST_SYSTEM_PROMPT,
        )
        data = self._extract_json_payload(content)
        return [DeepResearchAnalystProfile.model_validate(item) for item in data]

    async def run_research(
        self,
        topic: str,
        selected_analysts: list[dict],
        progress_callback: Any = None,
    ) -> dict:
        if progress_callback is not None:
            await progress_callback(30, "正在检索研究资料")
        search_results = await self.search(topic)
        if progress_callback is not None:
            await progress_callback(70, "正在生成研究报告")

        user_message = (
            f"主题：{topic}\n"
            f"分析师：{json.dumps(selected_analysts, ensure_ascii=False)}\n"
            f"搜索结果：{json.dumps(search_results, ensure_ascii=False)}"
        )
        final_report = await self.llm_client.chat(
            user_message=user_message,
            system_message=REPORT_SYSTEM_PROMPT,
        )
        if progress_callback is not None:
            await progress_callback(100, "报告已生成")

        return {
            "final_report": final_report,
            "sources": search_results,
        }


deepresearch_runner = DeepResearchRunner()
