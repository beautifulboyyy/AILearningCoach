import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.deps import get_current_active_user, get_db
from app.models.deepresearch import DeepResearchTask
from app.models.user import User
from main import app


@pytest_asyncio.fixture
async def api_user(async_session):
    user = User(
        username="api_deepresearch_user",
        email="api_deepresearch@example.com",
        password_hash="hashed",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def api_client(async_session, api_user):
    async def override_get_db():
        yield async_session

    async def override_get_current_user():
        return api_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_task_returns_drafting_summary(api_client, monkeypatch):
    from app.api.v1.endpoints import deepresearch

    class DummyDelay:
        def delay(self, *args, **kwargs):
            return None

    monkeypatch.setattr(deepresearch, "generate_analysts_task", DummyDelay())

    response = await api_client.post(
        "/api/v1/deepresearch/tasks",
        json={"topic": "如何设计 AI 学习教练"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "drafting_analysts"
    assert data["current_revision"] == 0


@pytest.mark.asyncio
async def test_get_task_detail_returns_current_analysts(api_client, api_user, async_session):
    from app.services.deepresearch_service import deepresearch_service

    task = await deepresearch_service.create_task(
        user_id=api_user.id,
        task_data={"topic": "详情测试", "requirements": None},
        db=async_session,
    )
    await deepresearch_service.finalize_analyst_revision(
        task_id=task.id,
        expected_revision=1,
        analysts=[{"name": "林老师", "role": "教学设计分析师", "affiliation": "高校", "description": "关注结构"}],
        feedback_text=None,
        db=async_session,
    )

    response = await api_client.get(f"/api/v1/deepresearch/tasks/{task.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["current_revision"] == 1
    assert data["remaining_feedback_rounds"] == 3
    assert data["analysts"][0]["name"] == "林老师"


@pytest.mark.asyncio
async def test_feedback_endpoint_rejects_exhausted_rounds(api_client, api_user, async_session):
    from app.services.deepresearch_service import deepresearch_service

    task = DeepResearchTask(
        user_id=api_user.id,
        topic="反馈耗尽",
        status="waiting_feedback",
        current_revision=4,
        feedback_round_used=3,
        max_feedback_rounds=3,
    )
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)

    response = await api_client.post(
        f"/api/v1/deepresearch/tasks/{task.id}/feedback",
        json={"feedback": "继续调整"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_start_endpoint_locks_revision(api_client, api_user, async_session, monkeypatch):
    from app.api.v1.endpoints import deepresearch
    from app.services.deepresearch_service import deepresearch_service

    class DummyDelay:
        def delay(self, *args, **kwargs):
            return None

    monkeypatch.setattr(deepresearch, "run_deepresearch_task", DummyDelay())

    task = await deepresearch_service.create_task(
        user_id=api_user.id,
        task_data={"topic": "启动测试", "requirements": None},
        db=async_session,
    )
    await deepresearch_service.finalize_analyst_revision(
        task_id=task.id,
        expected_revision=1,
        analysts=[{"name": "林老师", "role": "教学设计分析师", "affiliation": "高校", "description": "关注结构"}],
        feedback_text=None,
        db=async_session,
    )

    response = await api_client.post(f"/api/v1/deepresearch/tasks/{task.id}/start", json={"selected_revision": 1})

    assert response.status_code == 200
    data = response.json()
    assert data["selected_revision"] == 1
    assert data["status"] == "running_research"


@pytest.mark.asyncio
async def test_report_endpoint_rejects_unfinished_task(api_client, api_user, async_session):
    from app.services.deepresearch_service import deepresearch_service

    task = await deepresearch_service.create_task(
        user_id=api_user.id,
        task_data={"topic": "报告测试", "requirements": None},
        db=async_session,
    )

    response = await api_client.get(f"/api/v1/deepresearch/tasks/{task.id}/report")

    assert response.status_code == 409
