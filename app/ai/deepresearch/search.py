"""
DeepResearch 搜索适配层
"""
from typing import Any, List


class DeepResearchSearchAdapter:
    """固定双供应商搜索适配层"""

    def __init__(self, tavily_client: Any = None, bocha_client: Any = None):
        self.tavily_client = tavily_client
        self.bocha_client = bocha_client

    async def search(self, query: str) -> List[dict]:
        """执行搜索并返回统一结构结果"""
        results: List[dict] = []

        tavily_error = None
        if self.tavily_client is not None:
            try:
                results.extend(await self.tavily_client.search(query))
            except Exception as exc:  # pragma: no cover - 容错逻辑由调用测试覆盖
                tavily_error = exc

        if self.bocha_client is not None:
            try:
                results.extend(await self.bocha_client.search(query))
            except Exception:
                if tavily_error is not None and not results:
                    return []

        deduped: List[dict] = []
        seen_urls: set[str] = set()
        for item in results:
            url = item.get("url")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            deduped.append(item)

        return deduped
