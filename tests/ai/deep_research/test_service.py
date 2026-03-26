"""Deep Research Service层单元测试"""
import pytest

from app.ai.deep_research.service import DeepResearchService
from app.models.research_task import ResearchTask, ResearchStatus
from app.schemas.deep_research import StartResearchRequest


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_config():
    """模拟配置"""
    from unittest.mock import MagicMock
    config = MagicMock()
    config.max_turns = 3
    return config


@pytest.fixture
def service(mock_db, mock_config):
    """创建Service实例"""
    from unittest.mock import patch
    with patch("app.ai.deep_research.service.get_config", return_value=mock_config):
        svc = DeepResearchService(mock_db)
    return svc


@pytest.mark.asyncio
async def test_create_task_generates_thread_id(service, mock_db):
    """测试创建任务生成thread_id"""
    from unittest.mock import MagicMock

    request = StartResearchRequest(topic="LangGraph优势分析", max_analysts=3)

    await service.create_task(request)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    added_task = mock_db.add.call_args[0][0]
    assert added_task.thread_id.startswith("research_")
    assert added_task.topic == "LangGraph优势分析"
    assert added_task.max_analysts == 3
    assert added_task.status == ResearchStatus.PENDING


@pytest.mark.asyncio
async def test_create_task_with_analyst_directions(service, mock_db):
    """测试带方向的创建任务"""
    request = StartResearchRequest(
        topic="AI Agent分析",
        max_analysts=5,
        analyst_directions=["技术视角", "商业视角"]
    )

    await service.create_task(request)

    added_task = mock_db.add.call_args[0][0]
    assert added_task.analysts_config["directions"] == ["技术视角", "商业视角"]


@pytest.mark.asyncio
async def test_get_task_returns_task(service, mock_db):
    """测试获取存在的任务"""
    from unittest.mock import MagicMock

    mock_task = MagicMock()
    mock_task.thread_id = "research_123"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result

    result = await service.get_task_by_thread_id("research_123")

    assert result == mock_task
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_task_returns_none_for_missing(service, mock_db):
    """测试获取不存在的任务返回None"""
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    result = await service.get_task_by_thread_id("nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_list_tasks_returns_list(service, mock_db):
    """测试获取任务列表"""
    from unittest.mock import MagicMock

    mock_tasks = [MagicMock(), MagicMock()]
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_tasks
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    result = await service.list_tasks(limit=10)

    assert len(result) == 2
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_update_status_to_running(service, mock_db):
    """测试更新状态为running"""
    from unittest.mock import MagicMock

    mock_task = MagicMock()
    mock_task.status = ResearchStatus.PENDING
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result

    await service.update_task_status("research_123", ResearchStatus.RUNNING)

    assert mock_task.status == ResearchStatus.RUNNING
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_status_with_final_report(service, mock_db):
    """测试更新状态并设置final_report"""
    from unittest.mock import MagicMock

    mock_task = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result

    await service.update_task_status(
        "research_123",
        ResearchStatus.COMPLETED,
        final_report="# 测试报告"
    )

    assert mock_task.status == ResearchStatus.COMPLETED
    assert mock_task.final_report == "# 测试报告"


@pytest.mark.asyncio
async def test_update_status_task_not_found(service, mock_db):
    """测试更新不存在的任务"""
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    # 不应抛出异常，只是静默失败
    await service.update_task_status("nonexistent", ResearchStatus.RUNNING)
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_submit_feedback_with_text(service, mock_db):
    """测试提交具体反馈"""
    from unittest.mock import MagicMock, patch

    mock_task = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result

    with patch("app.ai.deep_research.service.research_graph") as mock_graph:
        result = await service.submit_feedback("research_123", "请增加技术视角")

    assert result["status"] == "continued"
    mock_graph.update_state.assert_called_once()
    call_args = mock_graph.update_state.call_args
    assert call_args[0][1]["human_analyst_feedback"] == "请增加技术视角"


@pytest.mark.asyncio
async def test_submit_feedback_empty_continues(service, mock_db):
    """测试空反馈继续执行"""
    from unittest.mock import MagicMock, patch

    mock_task = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result

    with patch("app.ai.deep_research.service.research_graph") as mock_graph:
        result = await service.submit_feedback("research_123", None)

    assert result["status"] == "continued"
    call_args = mock_graph.update_state.call_args
    assert call_args[0][1]["human_analyst_feedback"] is None


def test_classify_event_create_analysts(service):
    """测试分类create_analysts事件（使用astream_events格式）"""
    # astream_events 返回的事件格式
    event = {
        "event": "on_chain_start",
        "name": "create_analysts",
        "data": {}
    }

    result = service._classify_event(event)

    assert result["type"] == "status"
    assert "分析师" in result["data"]["message"]


def test_classify_event_unknown(service):
    """测试未知事件返回None"""
    event = {"unknown_node": {}}

    result = service._classify_event(event)

    assert result is None
