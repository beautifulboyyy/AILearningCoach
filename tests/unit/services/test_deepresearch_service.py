from datetime import datetime

import pytest
from sqlalchemy import select

from app.models.deepresearch import (
    DeepResearchAnalystRevision,
    DeepResearchRun,
    DeepResearchTask,
)
from app.models.user import User
from app.schemas.deepresearch import (
    DeepResearchFeedbackCreate,
    DeepResearchTaskCreate,
)
from app.services.deepresearch_service import (
    DeepResearchConflictError,
    DeepResearchService,
)


def test_feedback_round_used_matches_current_revision():
    task = DeepResearchTask(current_revision=3, feedback_round_used=2)

    assert task.feedback_round_used == task.current_revision - 1


def test_selected_revision_defaults_to_none():
    task = DeepResearchTask()

    assert task.selected_revision is None


def test_selected_revision_can_be_locked_to_specific_revision():
    task = DeepResearchTask(selected_revision=2)

    assert task.selected_revision == 2


def test_analyst_revision_exposes_selection_flag():
    revision = DeepResearchAnalystRevision(revision_number=2, is_selected=True)

    assert revision.revision_number == 2
    assert revision.is_selected is True


def test_research_run_tracks_revision_number():
    run = DeepResearchRun(revision_number=4)

    assert run.revision_number == 4


def test_task_create_schema_applies_default_max_analysts():
    payload = DeepResearchTaskCreate(topic="研究 AI 学习教练")

    assert payload.max_analysts == 4


def test_feedback_schema_rejects_blank_feedback():
    try:
        DeepResearchFeedbackCreate(feedback="   ")
    except Exception as exc:
        assert "feedback" in str(exc)
    else:
        raise AssertionError("blank feedback should be rejected")


def test_feedback_round_math_uses_current_revision_minus_one():
    service = DeepResearchService()

    assert service.calculate_feedback_round_used(current_revision=1) == 0
    assert service.calculate_feedback_round_used(current_revision=4) == 3


def test_remaining_feedback_rounds_never_below_zero():
    service = DeepResearchService()

    assert service.calculate_remaining_feedback_rounds(current_revision=1, max_feedback_rounds=3) == 3
    assert service.calculate_remaining_feedback_rounds(current_revision=4, max_feedback_rounds=3) == 0
    assert service.calculate_remaining_feedback_rounds(current_revision=6, max_feedback_rounds=3) == 0


def test_feedback_guard_raises_when_round_limit_is_exceeded():
    service = DeepResearchService()

    try:
        service.ensure_feedback_allowed(current_revision=4, max_feedback_rounds=3)
    except DeepResearchConflictError as exc:
        assert "反馈轮次已用尽" in str(exc)
    else:
        raise AssertionError("feedback guard should reject exhausted rounds")


@pytest.mark.asyncio
async def test_create_task_persists_drafting_task(async_session):
    service = DeepResearchService()
    user = User(
        username="deepresearch_user",
        email="deepresearch@example.com",
        password_hash="hashed",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    task = await service.create_task(
        user_id=user.id,
        task_data=DeepResearchTaskCreate(topic="研究 AI 教练").model_dump(),
        db=async_session,
    )

    assert task.user_id == user.id
    assert task.topic == "研究 AI 教练"
    assert task.current_revision == 0
    assert task.feedback_round_used == 0
    assert task.max_feedback_rounds == 3
    assert task.progress_message == "正在生成分析师草案"


@pytest.mark.asyncio
async def test_create_task_rejects_second_running_task(async_session):
    service = DeepResearchService()
    user = User(
        username="busy_user",
        email="busy@example.com",
        password_hash="hashed",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    await service.create_task(
        user_id=user.id,
        task_data=DeepResearchTaskCreate(topic="第一个任务").model_dump(),
        db=async_session,
    )

    with pytest.raises(DeepResearchConflictError):
        await service.create_task(
            user_id=user.id,
            task_data=DeepResearchTaskCreate(topic="第二个任务").model_dump(),
            db=async_session,
        )


@pytest.mark.asyncio
async def test_finalize_analyst_revision_creates_revision_one(async_session):
    service = DeepResearchService()
    user = User(
        username="revision_user",
        email="revision@example.com",
        password_hash="hashed",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    task = await service.create_task(
        user_id=user.id,
        task_data=DeepResearchTaskCreate(topic="分析师生成").model_dump(),
        db=async_session,
    )

    finalized = await service.finalize_analyst_revision(
        task_id=task.id,
        expected_revision=1,
        analysts=[{"name": "林老师", "role": "教学设计分析师", "affiliation": "高校", "description": "关注结构"}],
        feedback_text=None,
        db=async_session,
    )

    assert finalized.current_revision == 1
    assert finalized.feedback_round_used == 0
    assert finalized.progress_message == "已生成分析师草案，等待反馈"

    result = await async_session.execute(
        select(DeepResearchAnalystRevision).where(DeepResearchAnalystRevision.task_id == task.id)
    )
    revisions = result.scalars().all()
    assert len(revisions) == 1
    assert revisions[0].revision_number == 1


@pytest.mark.asyncio
async def test_submit_feedback_persists_pending_feedback_and_history(async_session):
    service = DeepResearchService()
    user = User(
        username="feedback_user",
        email="feedback@example.com",
        password_hash="hashed",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    task = await service.create_task(
        user_id=user.id,
        task_data=DeepResearchTaskCreate(topic="反馈闭环", max_analysts=3).model_dump(),
        db=async_session,
    )
    await service.finalize_analyst_revision(
        task_id=task.id,
        expected_revision=1,
        analysts=[{"name": "林老师", "role": "教学设计分析师", "affiliation": "高校", "description": "关注结构"}],
        feedback_text=None,
        db=async_session,
    )

    updated_task = await service.submit_feedback(
        task_id=task.id,
        user_id=user.id,
        feedback="增加偏工程落地的分析视角",
        db=async_session,
    )
    assert updated_task.pending_feedback_text == "增加偏工程落地的分析视角"

    feedback_history = await service.get_feedback_history(task_id=task.id, db=async_session)
    assert feedback_history == ["增加偏工程落地的分析视角"]

    finalized = await service.finalize_analyst_revision(
        task_id=task.id,
        expected_revision=2,
        analysts=[{"name": "周工", "role": "架构分析师", "affiliation": "企业", "description": "关注工程化"}],
        feedback_text=updated_task.pending_feedback_text,
        db=async_session,
    )
    assert finalized.current_revision == 2
    assert finalized.pending_feedback_text is None

    result = await async_session.execute(
        select(DeepResearchAnalystRevision)
        .where(DeepResearchAnalystRevision.task_id == task.id)
        .order_by(DeepResearchAnalystRevision.revision_number)
    )
    revisions = result.scalars().all()
    assert revisions[1].feedback_text == "增加偏工程落地的分析视角"


@pytest.mark.asyncio
async def test_start_research_locks_selected_revision_and_selection_flags(async_session):
    service = DeepResearchService()
    user = User(
        username="start_user",
        email="start@example.com",
        password_hash="hashed",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    task = await service.create_task(
        user_id=user.id,
        task_data=DeepResearchTaskCreate(topic="启动研究").model_dump(),
        db=async_session,
    )
    await service.finalize_analyst_revision(
        task_id=task.id,
        expected_revision=1,
        analysts=[{"name": "林老师", "role": "教学设计分析师", "affiliation": "高校", "description": "关注结构"}],
        feedback_text=None,
        db=async_session,
    )
    await service.submit_feedback(
        task_id=task.id,
        user_id=user.id,
        feedback="改成更偏技术实现",
        db=async_session,
    )
    await service.finalize_analyst_revision(
        task_id=task.id,
        expected_revision=2,
        analysts=[{"name": "周工", "role": "架构分析师", "affiliation": "企业", "description": "关注技术方案"}],
        feedback_text="改成更偏技术实现",
        db=async_session,
    )

    started = await service.start_research(
        task_id=task.id,
        user_id=user.id,
        selected_revision=2,
        db=async_session,
    )

    assert started.selected_revision == 2
    assert started.current_revision == 2

    result = await async_session.execute(
        select(DeepResearchAnalystRevision)
        .where(DeepResearchAnalystRevision.task_id == task.id)
        .order_by(DeepResearchAnalystRevision.revision_number)
    )
    revisions = result.scalars().all()
    assert [item.is_selected for item in revisions] == [False, True]


@pytest.mark.asyncio
async def test_mark_task_failed_skips_when_selected_revision_is_stale(async_session):
    service = DeepResearchService()
    user = User(
        username="stale_fail_user",
        email="stale-fail@example.com",
        password_hash="hashed",
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    task = await service.create_task(
        user_id=user.id,
        task_data=DeepResearchTaskCreate(topic="失败保护").model_dump(),
        db=async_session,
    )
    await service.finalize_analyst_revision(
        task_id=task.id,
        expected_revision=1,
        analysts=[{"name": "林老师", "role": "教学设计分析师", "affiliation": "高校", "description": "关注结构"}],
        feedback_text=None,
        db=async_session,
    )
    await service.start_research(
        task_id=task.id,
        user_id=user.id,
        selected_revision=1,
        db=async_session,
    )

    await service.mark_task_failed(
        task_id=task.id,
        message="旧 worker 失败",
        db=async_session,
        expected_status="running_research",
        selected_revision=2,
    )

    refreshed_task = await service.get_task(task_id=task.id, user_id=user.id, db=async_session)
    assert refreshed_task.status.value == "running_research"
    assert refreshed_task.error_message is None
