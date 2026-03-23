"""
DeepResearch 搜索适配层
"""
from __future__ import annotations

from typing import Any, List

import httpx

from app.core.config import settings


class TavilySearchClient:
    """Tavily 搜索客户端"""

    def __init__(self, api_key: str, base_url: str = "https://api.tavily.com/search"):
        self.api_key = api_key
        self.base_url = base_url

    async def search(self, query: str) -> list[dict]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "topic": "general",
            "search_depth": "basic",
            "max_results": 5,
            "include_raw_content": False,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        normalized: list[dict] = []
        for item in data.get("results", []):
            normalized.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "source": item.get("url", ""),
                    "provider": "tavily",
                }
            )
        return normalized


class BochaSearchClient:
    """博查搜索客户端"""

    def __init__(self, api_key: str, base_url: str = "https://api.bochaai.com/v1/web-search"):
        self.api_key = api_key
        self.base_url = base_url

    async def search(self, query: str) -> list[dict]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "summary": True,
            "count": 5,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        normalized: list[dict] = []
        for item in data.get("webPages", {}).get("value", []):
            normalized.append(
                {
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "content": item.get("summary") or item.get("snippet", ""),
                    "source": item.get("siteName", ""),
                    "provider": "bocha",
                }
            )
        return normalized


class DeepResearchSearchAdapter:
    """固定双供应商搜索适配层"""

    def __init__(self, tavily_client: Any = None, bocha_client: Any = None):
        self.tavily_client = tavily_client
        self.bocha_client = bocha_client

    @classmethod
    def from_settings(cls) -> "DeepResearchSearchAdapter":
        tavily_client = TavilySearchClient(settings.TAVILY_API_KEY) if settings.TAVILY_API_KEY else None
        bocha_client = BochaSearchClient(settings.BOCHA_API_KEY) if settings.BOCHA_API_KEY else None
        return cls(tavily_client=tavily_client, bocha_client=bocha_client)

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
