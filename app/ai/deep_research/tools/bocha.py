"""Bocha 搜索工具"""
import os
from typing import List

import httpx
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class BochaSearchInput(BaseModel):
    """Bocha搜索输入"""
    query: str = Field(description="搜索查询")
    count: int = Field(default=10, ge=1, le=50)
    freshness: str = Field(default="noLimit")
    summary: bool = Field(default=False)


class BochaSearchTool(BaseTool):
    """Bocha搜索工具 - Custom Tool"""

    name: str = "bocha_search"
    description: str = "从全网搜索网页信息和链接，返回搜索结果"
    args_schema: type[BaseModel] = BochaSearchInput

    def _search(self, query: str, count: int = 10, freshness: str = "noLimit", summary: bool = False) -> List[dict]:
        """执行Bocha搜索"""
        api_key = os.getenv("BOCHA_API_KEY")
        if not api_key:
            raise ValueError("BOCHA_API_KEY not found in environment")

        url = "https://api.bocha.cn/v1/web-search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "count": count,
            "freshness": freshness,
            "summary": summary
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        web_pages = data.get("webPages", {})
        results = web_pages.get("value", [])

        return [
            {
                "url": r.get("url", ""),
                "name": r.get("name", ""),
                "snippet": r.get("snippet", ""),
                "siteName": r.get("siteName", ""),
            }
            for r in results
        ]

    def _run(self, query: str, count: int = 10, freshness: str = "noLimit", summary: bool = False) -> str:
        """同步执行搜索"""
        results = self._search(query, count, freshness, summary)
        formatted = "\n\n".join([
            f'<Document href="{r["url"]}"/>\n{r["name"]}\n{r["snippet"]}'
            for r in results
        ])
        return formatted

    async def _arun(self, query: str, count: int = 10, freshness: str = "noLimit", summary: bool = False) -> str:
        """异步执行搜索"""
        results = await self._async_search(query, count, freshness, summary)
        formatted = "\n\n".join([
            f'<Document href="{r["url"]}"/>\n{r["name"]}\n{r["snippet"]}'
            for r in results
        ])
        return formatted

    async def _async_search(self, query: str, count: int, freshness: str, summary: bool) -> List[dict]:
        """异步HTTP请求"""
        api_key = os.getenv("BOCHA_API_KEY")
        if not api_key:
            raise ValueError("BOCHA_API_KEY not found in environment")

        url = "https://api.bocha.cn/v1/web-search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "count": count,
            "freshness": freshness,
            "summary": summary
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        web_pages = data.get("webPages", {})
        results = web_pages.get("value", [])

        return [
            {
                "url": r.get("url", ""),
                "name": r.get("name", ""),
                "snippet": r.get("snippet", ""),
                "siteName": r.get("siteName", ""),
            }
            for r in results
        ]
