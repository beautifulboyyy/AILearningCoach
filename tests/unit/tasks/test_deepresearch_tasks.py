from types import SimpleNamespace

import pytest


class FakeSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSessionFactory:
    def __init__(self, session):
        self.session = session

    def __call__(self):
        return FakeSessionContext(self.session)


@pytest.mark.asyncio
async def test_generate_analysts_task_skips_when_finalize_returns_none(monkeypatch):
    from app.tasks import deepresearch_tasks

    session = object()
    monkeypatch.setattr(deepresearch_tasks, "async_session_maker", FakeSessionFactory(session))

    calls = {"runner": 0}

    async def fake_get_task_for_execution(task_id, db, expected_status=None):
        return SimpleNamespace(id=task_id, topic="主题", requirements=None)

    async def fake_generate_analysts(**kwargs):
        calls["runner"] += 1
        return [{"name": "林老师", "role": "教学设计", "affiliation": "高校", "description": "关注结构"}]

    async def fake_finalize_analyst_revision(**kwargs):
        return None

    monkeypatch.setattr(deepresearch_tasks.deepresearch_service, "get_task_for_execution", fake_get_task_for_execution)
    monkeypatch.setattr(deepresearch_tasks.deepresearch_runner, "generate_analysts", fake_generate_analysts)
    monkeypatch.setattr(deepresearch_tasks.deepresearch_service, "finalize_analyst_revision", fake_finalize_analyst_revision)

    result = await deepresearch_tasks._generate_analysts_task(
        task_id=1,
        expected_revision=1,
        expected_status="drafting_analysts",
    )

    assert result["status"] == "stale"
    assert calls["runner"] == 1


@pytest.mark.asyncio
async def test_run_deepresearch_task_returns_completed_payload(monkeypatch):
    from app.tasks import deepresearch_tasks

    session = object()
    monkeypatch.setattr(deepresearch_tasks, "async_session_maker", FakeSessionFactory(session))

    async def fake_get_task_for_execution(task_id, db, expected_status=None):
        return SimpleNamespace(
            id=task_id,
            topic="主题",
            selected_revision=2,
            current_revision=2,
        )

    async def fake_get_selected_analysts(task_id, selected_revision, db):
        return [{"name": "周工", "role": "架构分析师", "affiliation": "企业", "description": "关注技术方案"}]

    async def fake_run_research(**kwargs):
        return {"final_report": "# 报告", "sources": []}

    async def fake_finalize_research_run(**kwargs):
        return {"status": "completed"}

    monkeypatch.setattr(deepresearch_tasks.deepresearch_service, "get_task_for_execution", fake_get_task_for_execution)
    monkeypatch.setattr(deepresearch_tasks.deepresearch_service, "get_selected_analysts", fake_get_selected_analysts)
    monkeypatch.setattr(deepresearch_tasks.deepresearch_runner, "run_research", fake_run_research)
    monkeypatch.setattr(deepresearch_tasks.deepresearch_service, "finalize_research_run", fake_finalize_research_run)

    result = await deepresearch_tasks._run_deepresearch_task(
        task_id=1,
        selected_revision=2,
        expected_status="running_research",
    )

    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_run_deepresearch_task_marks_failure_when_runner_raises(monkeypatch):
    from app.tasks import deepresearch_tasks

    session = object()
    monkeypatch.setattr(deepresearch_tasks, "async_session_maker", FakeSessionFactory(session))

    async def fake_get_task_for_execution(task_id, db, expected_status=None):
        return SimpleNamespace(
            id=task_id,
            topic="主题",
            selected_revision=2,
            current_revision=2,
        )

    async def fake_get_selected_analysts(task_id, selected_revision, db):
        return [{"name": "周工", "role": "架构分析师", "affiliation": "企业", "description": "关注技术方案"}]

    async def fake_run_research(**kwargs):
        raise RuntimeError("runner error")

    captured = {}

    async def fake_mark_task_failed(task_id, message, db):
        captured["message"] = message

    monkeypatch.setattr(deepresearch_tasks.deepresearch_service, "get_task_for_execution", fake_get_task_for_execution)
    monkeypatch.setattr(deepresearch_tasks.deepresearch_service, "get_selected_analysts", fake_get_selected_analysts)
    monkeypatch.setattr(deepresearch_tasks.deepresearch_runner, "run_research", fake_run_research)
    monkeypatch.setattr(deepresearch_tasks.deepresearch_service, "mark_task_failed", fake_mark_task_failed)

    result = await deepresearch_tasks._run_deepresearch_task(
        task_id=1,
        selected_revision=2,
        expected_status="running_research",
    )

    assert result["status"] == "failed"
    assert "runner error" in captured["message"]
