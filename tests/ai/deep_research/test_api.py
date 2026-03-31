"""Deep Research API集成测试"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestDeepResearchAPI:
    """Deep Research API端点测试"""

    def test_list_research_tasks_empty(self, client):
        """测试获取空的任务列表"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.list_tasks = AsyncMock(return_value=[])
            mock_service.return_value = mock_instance

            response = client.get("/api/v1/deep-research/tasks")

            assert response.status_code == 200
            assert response.json() == []

    def test_start_research(self, client):
        """测试开始新研究任务"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_task = MagicMock()
            mock_task.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_task.thread_id = "test-thread-123"
            mock_task.topic = "LangGraph优势分析"
            mock_task.status = "pending"
            mock_task.max_analysts = 3
            mock_task.max_turns = 3
            mock_task.final_report = None
            mock_task.created_at = "2026-03-25T10:00:00"
            mock_task.updated_at = "2026-03-25T10:00:00"

            mock_instance.create_task = AsyncMock(return_value=mock_task)
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/v1/deep-research/tasks",
                json={"topic": "LangGraph优势分析", "max_analysts": 3}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "test-thread-123"
            assert data["topic"] == "LangGraph优势分析"
            assert data["status"] == "pending"

    def test_get_research_task(self, client):
        """测试获取特定研究任务"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_task = MagicMock()
            mock_task.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_task.thread_id = "test-thread-123"
            mock_task.topic = "LangGraph优势分析"
            mock_task.status = "running"
            mock_task.max_analysts = 3
            mock_task.max_turns = 3
            mock_task.analysts_config = {"analysts": []}
            mock_task.final_report = None
            mock_task.created_at = "2026-03-25T10:00:00"
            mock_task.updated_at = "2026-03-25T10:00:00"

            mock_instance.get_task_by_thread_id = AsyncMock(return_value=mock_task)
            mock_service.return_value = mock_instance

            response = client.get("/api/v1/deep-research/tasks/test-thread-123")

            assert response.status_code == 200
            data = response.json()
            assert data["thread_id"] == "test-thread-123"
            assert data["status"] == "running"

    def test_get_research_task_includes_awaiting_feedback_analysts(self, client):
        """测试任务详情会返回等待确认的分析师快照"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_task = MagicMock()
            mock_task.id = "550e8400-e29b-41d4-a716-446655440000"
            mock_task.thread_id = "test-thread-123"
            mock_task.topic = "LangGraph优势分析"
            mock_task.status = "awaiting_feedback"
            mock_task.max_analysts = 3
            mock_task.max_turns = 3
            mock_task.analysts_config = {
                "analysts": [{"name": "A", "affiliation": "Org", "role": "R", "description": "D"}]
            }
            mock_task.final_report = None
            mock_task.created_at = "2026-03-25T10:00:00"
            mock_task.updated_at = "2026-03-25T10:00:00"
            mock_instance.get_task_by_thread_id = AsyncMock(return_value=mock_task)
            mock_service.return_value = mock_instance

            response = client.get("/api/v1/deep-research/tasks/test-thread-123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "awaiting_feedback"
            assert data["analysts"][0]["name"] == "A"

    def test_get_research_task_not_found(self, client):
        """测试获取不存在的任务"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_task_by_thread_id = AsyncMock(return_value=None)
            mock_service.return_value = mock_instance

            response = client.get("/api/v1/deep-research/tasks/nonexistent-thread")

            assert response.status_code == 404

    def test_generate_analysts(self, client):
        """测试生成分析师流程"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_task = MagicMock()
            mock_instance.get_task_by_thread_id = AsyncMock(return_value=mock_task)
            mock_instance.generate_analysts = AsyncMock(return_value={
                "status": "awaiting_feedback",
                "thread_id": "test-thread-123",
                "analysts": [{"name": "A", "affiliation": "Org", "role": "R", "description": "D"}],
                "interrupt_required": True,
            })
            mock_service.return_value = mock_instance

            response = client.post("/api/v1/deep-research/tasks/test-thread-123/analysts")

            assert response.status_code == 200
            assert response.json()["status"] == "awaiting_feedback"

    def test_submit_feedback(self, client):
        """测试提交人类反馈"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_task = MagicMock()
            mock_task.status = "awaiting_feedback"
            mock_instance.get_task_by_thread_id = AsyncMock(return_value=mock_task)
            mock_instance.submit_feedback = AsyncMock(return_value={
                "status": "awaiting_feedback",
                "thread_id": "test-thread-123",
                "analysts": [{"name": "A", "affiliation": "Org", "role": "R", "description": "D"}],
                "message": "已根据反馈重新生成分析师",
            })
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/v1/deep-research/tasks/test-thread-123/feedback",
                json={"action": "regenerate", "feedback": "请增加更多技术视角的分析"}
            )

            assert response.status_code == 200
            assert response.json()["status"] == "awaiting_feedback"

    def test_submit_feedback_requires_feedback_when_regenerate(self, client):
        """测试重新生成分析师时必须提供自然语言反馈"""
        response = client.post(
            "/api/v1/deep-research/tasks/test-thread-123/feedback",
            json={"action": "regenerate"}
        )

        assert response.status_code == 422

    def test_submit_feedback_requires_awaiting_feedback_status(self, client):
        """测试只有等待反馈状态的任务才允许提交反馈"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_task = MagicMock()
            mock_task.status = "pending"
            mock_instance.get_task_by_thread_id = AsyncMock(return_value=mock_task)
            mock_service.return_value = mock_instance

            response = client.post(
                "/api/v1/deep-research/tasks/test-thread-123/feedback",
                json={"action": "approve"}
            )

            assert response.status_code == 409

    def test_cancel_research(self, client):
        """测试删除研究任务"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.delete_task = AsyncMock(return_value=True)
            mock_service.return_value = mock_instance

            response = client.delete("/api/v1/deep-research/tasks/test-thread-123")

            assert response.status_code == 200
            assert response.json()["status"] == "deleted"

    def test_cancel_research_not_found(self, client):
        """测试删除不存在的任务"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.delete_task = AsyncMock(return_value=False)
            mock_service.return_value = mock_instance

            response = client.delete("/api/v1/deep-research/tasks/nonexistent-thread")

            assert response.status_code == 404

    def test_stream_research_events_not_found(self, client):
        """测试SSE流不存在任务"""
        with patch("app.api.v1.endpoints.deep_research.DeepResearchService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_task_by_thread_id = AsyncMock(return_value=None)
            mock_service.return_value = mock_instance

            response = client.get("/api/v1/deep-research/nonexistent-thread/events")

            assert response.status_code == 404
