"""Deep Research Service层单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.deep_research.service import DeepResearchService
from app.models.research_task import ResearchStatus
from app.schemas.deep_research import StartResearchRequest


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_config():
    """模拟配置"""
    config = MagicMock()
    config.max_turns = 3
    return config


@pytest.fixture
def service(mock_db, mock_config):
    """创建Service实例"""
    with patch("app.ai.deep_research.service.get_config", return_value=mock_config):
        svc = DeepResearchService(mock_db)
    return svc


def test_progress_defaults_to_idle_when_missing(service):
    """测试未写入进度时返回 idle 占位"""
    progress = service.get_progress("research_123")

    assert progress["thread_id"] == "research_123"
    assert progress["stage"] == "idle"
    assert progress["message"] == ""


def test_progress_can_be_updated_and_cleared(service):
    """测试运行时进度可更新且可清空"""
    service.update_progress("research_123", "searching", "正在并行检索 Tavily 和 Bocha")

    progress = service.get_progress("research_123")
    assert progress["stage"] == "searching"
    assert "Tavily" in progress["message"]

    service.clear_progress("research_123")

    cleared = service.get_progress("research_123")
    assert cleared["stage"] == "idle"


@pytest.mark.asyncio
async def test_create_task_generates_thread_id(service, mock_db):
    """测试创建任务生成thread_id"""
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
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    result = await service.get_task_by_thread_id("nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_list_tasks_returns_list(service, mock_db):
    """测试获取任务列表"""
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
async def test_delete_task_removes_record(service, mock_db):
    """测试删除任务会从数据库中移除记录"""
    mock_task = MagicMock()
    mock_task.thread_id = "research_123"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result
    mock_db.delete = AsyncMock()

    deleted = await service.delete_task("research_123")

    assert deleted is True
    mock_db.delete.assert_awaited_once_with(mock_task)
    mock_db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_delete_task_returns_false_when_missing(service, mock_db):
    """测试删除不存在任务时返回False"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    mock_db.delete = AsyncMock()

    deleted = await service.delete_task("missing")

    assert deleted is False
    mock_db.delete.assert_not_called()


@pytest.mark.asyncio
async def test_update_status_to_running(service, mock_db):
    """测试更新状态为running"""
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
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    # 不应抛出异常，只是静默失败
    await service.update_task_status("nonexistent", ResearchStatus.RUNNING)
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_submit_feedback_with_text(service, mock_db):
    """测试提交具体反馈会重新生成分析师并继续等待确认"""
    mock_task = MagicMock()
    mock_task.thread_id = "research_123"
    mock_task.topic = "测试主题"
    mock_task.max_analysts = 3
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result

    with patch("app.ai.deep_research.service.research_graph") as mock_graph:
        mock_graph.invoke.return_value = {
            "__interrupt__": [{"value": {"analysts": [{"name": "A", "affiliation": "Org", "role": "R", "description": "D"}]}}]
        }
        mock_graph.get_state.return_value = MagicMock(
            values={
                "analysts": [{"name": "A", "affiliation": "Org", "role": "R", "description": "D"}]
            }
        )
        service.update_task_status = AsyncMock()

        result = await service.submit_feedback("research_123", "请增加技术视角")

    assert result["status"] == "awaiting_feedback"
    assert result["analysts"][0]["name"] == "A"
    command = mock_graph.invoke.call_args.args[0]
    assert command.resume["action"] == "regenerate"
    assert command.resume["feedback"] == "请增加技术视角"
    service.update_task_status.assert_awaited_with("research_123", ResearchStatus.AWAITING_FEEDBACK)


@pytest.mark.asyncio
async def test_submit_feedback_empty_continues(service, mock_db):
    """测试确认满意后继续执行研究"""
    mock_task = MagicMock()
    mock_task.thread_id = "research_123"
    mock_task.topic = "测试主题"
    mock_task.max_analysts = 3
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result

    service._handle_graph_result = AsyncMock(return_value={"status": "completed", "thread_id": "research_123"})

    service._invoke_graph_in_executor = AsyncMock(return_value={"final_report": "# 报告", "sections": ["A"]})

    with patch("app.ai.deep_research.service.research_graph"):
        result = await service.submit_feedback("research_123", None)

    assert result["status"] == "completed"
    command = service._invoke_graph_in_executor.await_args.args[0]
    assert command.resume["action"] == "approve"
    service._handle_graph_result.assert_awaited()


@pytest.mark.asyncio
async def test_generate_analysts_sets_awaiting_feedback(service, mock_db):
    """测试生成分析师后任务进入等待反馈状态"""
    mock_task = MagicMock()
    mock_task.thread_id = "research_123"
    mock_task.topic = "测试主题"
    mock_task.max_analysts = 2
    mock_task.analysts_config = {}
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result
    service.update_task_status = AsyncMock()

    with patch("app.ai.deep_research.service.research_graph") as mock_graph:
        mock_graph.invoke.return_value = {
            "__interrupt__": [{"value": {"analysts": [{"name": "A", "affiliation": "Org", "role": "R", "description": "D"}]}}]
        }
        mock_graph.get_state.return_value = MagicMock(
            values={
                "analysts": [{"name": "A", "affiliation": "Org", "role": "R", "description": "D"}]
            }
        )

        result = await service.generate_analysts("research_123")

    assert result["status"] == "awaiting_feedback"
    assert result["thread_id"] == "research_123"
    assert result["analysts"][0]["name"] == "A"
    service.update_task_status.assert_awaited_with("research_123", ResearchStatus.AWAITING_FEEDBACK)
    assert mock_task.analysts_config["analysts"][0]["name"] == "A"


@pytest.mark.asyncio
async def test_generate_analysts_uses_task_max_turns(service, mock_db):
    """测试生成分析师时会把任务的最大访谈轮次写入图状态"""
    mock_task = MagicMock()
    mock_task.thread_id = "research_123"
    mock_task.topic = "测试主题"
    mock_task.max_analysts = 2
    mock_task.max_turns = 6
    mock_task.analysts_config = {}
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_task
    mock_db.execute.return_value = mock_result
    service._handle_graph_result = AsyncMock(
        return_value={"status": "awaiting_feedback", "thread_id": "research_123", "analysts": []}
    )

    with patch("app.ai.deep_research.service.research_graph") as mock_graph:
        mock_graph.invoke.return_value = {"__interrupt__": []}

        await service.generate_analysts("research_123")

    initial_state = mock_graph.invoke.call_args.args[0]
    assert initial_state["max_num_turns"] == 6


