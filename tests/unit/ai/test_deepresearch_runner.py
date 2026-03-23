import pytest

from app.services.deepresearch_runner import DeepResearchRunner


class FakeLLM:
    async def chat(self, user_message: str, system_message: str = None, **kwargs):
        if "生成分析师" in user_message:
            return """
            [
              {
                "affiliation": "高校",
                "name": "林老师",
                "role": "教学设计分析师",
                "description": "关注课程结构和学习动机"
              }
            ]
            """
        return "# 最终报告\n\n这是研究结果。"


class FakeSearchService:
    def __init__(self, tavily_result=None, bocha_result=None, tavily_error=None, bocha_error=None):
        self.tavily_result = tavily_result or []
        self.bocha_result = bocha_result or []
        self.tavily_error = tavily_error
        self.bocha_error = bocha_error

    async def search(self, query: str):
        if self.tavily_error and self.bocha_error:
            return []
        if self.tavily_error:
            return self.bocha_result
        if self.bocha_error:
            return self.tavily_result
        return self.tavily_result + self.bocha_result


@pytest.mark.asyncio
async def test_generate_analysts_returns_structured_items():
    runner = DeepResearchRunner(llm_client=FakeLLM(), search_service=FakeSearchService())

    analysts = await runner.generate_analysts(
        topic="如何设计 AI 学习教练",
        requirements="偏教学设计",
        max_analysts=4,
        feedback_history=[],
    )

    assert len(analysts) == 1
    assert analysts[0].name == "林老师"
    assert analysts[0].role == "教学设计分析师"


@pytest.mark.asyncio
async def test_run_research_returns_markdown_report():
    runner = DeepResearchRunner(llm_client=FakeLLM(), search_service=FakeSearchService())

    result = await runner.run_research(
        topic="如何设计 AI 学习教练",
        selected_analysts=[
            {
                "affiliation": "高校",
                "name": "林老师",
                "role": "教学设计分析师",
                "description": "关注课程结构和学习动机",
            }
        ],
    )

    assert result["final_report"].startswith("# 最终报告")


@pytest.mark.asyncio
async def test_search_falls_back_to_bocha_when_tavily_fails():
    runner = DeepResearchRunner(
        llm_client=FakeLLM(),
        search_service=FakeSearchService(
            tavily_error=RuntimeError("tavily down"),
            bocha_result=[{"title": "博查结果", "url": "https://bocha.test", "content": "内容", "provider": "bocha"}],
        ),
    )

    results = await runner.search("AI 学习教练")

    assert len(results) == 1
    assert results[0]["provider"] == "bocha"


@pytest.mark.asyncio
async def test_search_returns_empty_when_all_providers_fail():
    runner = DeepResearchRunner(
        llm_client=FakeLLM(),
        search_service=FakeSearchService(
            tavily_error=RuntimeError("tavily down"),
            bocha_error=RuntimeError("bocha down"),
        ),
    )

    results = await runner.search("AI 学习教练")

    assert results == []
