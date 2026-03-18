"""
对话相关API
"""
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
import json
import hashlib

from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.conversation import Conversation, Message, MessageRole
from app.models.profile import UserProfile
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistory, Source
from app.ai.rag.generator import rag_generator
from app.ai.agents.orchestrator import agent_orchestrator
from app.ai.memory.manager import memory_manager
from app.services.conversation_summary_service import conversation_summary_service
from app.services.progress_service import progress_service
from app.utils.cache import cache_get
from app.utils.logger import app_logger

router = APIRouter()

RECENT_HISTORY_LIMIT = 6
SHORT_MEMORY_LIMIT = 3
SUMMARY_TRIGGER_INTERVAL = 6


async def _load_recent_history(
    db: AsyncSession,
    conversation_id: int,
    limit: int = RECENT_HISTORY_LIMIT
) -> List[Dict[str, str]]:
    """
    读取最近N条消息并按时间正序返回。
    """
    result = await db.execute(
        select(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.desc()
        ).limit(limit)
    )
    messages = list(result.scalars().all())
    messages.reverse()

    recent_history: List[Dict[str, str]] = []
    for msg in messages:
        recent_history.append({
            "role": msg.role.value,
            "content": msg.content
        })
    return recent_history


async def _load_short_term_memory(session_id: str) -> List[Dict[str, Any]]:
    """
    加载短期会话记忆，优先返回“窗口外”的近期信息。
    """
    memories = await memory_manager.get_short_term_memory(session_id)
    if not memories:
        return []

    # recent_history内容会在调用方传入context，此处只负责按结构筛选
    return memories


def _normalize_for_match(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.strip().split()).lower()[:120]


def _fingerprint(text: str) -> str:
    """
    生成稳定短指纹，避免在Redis重复存储原文。
    """
    normalized = _normalize_for_match(text)
    if not normalized:
        return ""
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]


def _select_window_external_memory(
    memories: List[Dict[str, Any]],
    recent_history: List[Dict[str, str]],
    limit: int = SHORT_MEMORY_LIMIT
) -> List[Dict[str, Any]]:
    """
    选择窗口外记忆，避免与recent_history重复。
    """
    recent_fingerprints = {
        _fingerprint(item.get("content", ""))
        for item in recent_history
        if isinstance(item, dict) and item.get("content")
    }

    selected: List[Dict[str, Any]] = []
    for memory in reversed(memories):  # 从新到旧找窗口外记忆
        metadata = memory.get("metadata") if isinstance(memory, dict) else {}
        if not isinstance(metadata, dict):
            metadata = {}

        user_fp = metadata.get("user_fp", "")
        assistant_fp = metadata.get("assistant_fp", "")
        memory_fp = metadata.get("memory_fp", "")

        overlap = (
            user_fp in recent_fingerprints or
            assistant_fp in recent_fingerprints or
            memory_fp in recent_fingerprints
        )
        if overlap:
            continue

        selected.append(memory)
        if len(selected) >= limit:
            break

    selected.reverse()  # 恢复时间正序
    return selected


async def _load_conversation_summary(conversation: Conversation, session_id: str) -> Optional[str]:
    """
    加载会话摘要，优先DB，DB无值时回退Redis热摘要。
    """
    if conversation.summary:
        return conversation.summary

    summary_key = f"session:{session_id}:summary"
    cached_summary = await cache_get(summary_key)
    if isinstance(cached_summary, str) and cached_summary.strip():
        return cached_summary.strip()
    return None


async def _save_short_term_memory(
    user_id: int,
    session_id: str,
    user_message: str,
    assistant_message: str,
    intent: str,
    agent: str
):
    """
    写入结构化Redis短期记忆。
    """
    user_fp = _fingerprint(user_message)
    assistant_fp = _fingerprint(assistant_message)
    memory_text = f"用户问：{user_message[:180]} | 助手答：{assistant_message[:180]}"

    memory_record = {
        "intent": intent,
        "agent": agent,
        "user_fp": user_fp,
        "assistant_fp": assistant_fp,
        "memory_fp": _fingerprint(memory_text)
    }

    await memory_manager.save_short_term_memory(
        user_id=user_id,
        session_id=session_id,
        content=memory_text,
        metadata=memory_record
    )


async def _trigger_summary_update(
    conversation_id: int,
    session_id: str,
    force_fallback: bool = False
):
    """
    触发摘要更新：优先Celery，同时提供进程内兜底。
    """
    celery_triggered = False
    try:
        from app.tasks.async_tasks import update_conversation_summary
        update_conversation_summary.delay(
            conversation_id=conversation_id,
            session_id=session_id
        )
        celery_triggered = True
        app_logger.info("已触发会话摘要更新任务（Celery）")
    except Exception as e:
        app_logger.warning(f"触发会话摘要更新任务失败: {e}")

    # 兜底：Celery不可用或需要强制兜底时，进程内异步更新，避免summary长期为空
    if force_fallback or not celery_triggered:
        async def _fallback():
            await conversation_summary_service.update_conversation_summary(
                conversation_id=conversation_id,
                session_id=session_id,
                message_limit=20
            )
        asyncio.create_task(_fallback())
        app_logger.info("已触发会话摘要更新任务（In-Process Fallback）")


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    对话接口（非流式）
    
    发送消息并获取回复
    """
    try:
        # 1. 获取或创建会话
        session_id = request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            conversation = Conversation(
                user_id=current_user.id,
                session_id=session_id,
                started_at=datetime.utcnow(),
                message_count=0
            )
            db.add(conversation)
            await db.flush()
        else:
            result = await db.execute(
                select(Conversation).filter(
                    Conversation.session_id == session_id,
                    Conversation.user_id == current_user.id
                )
            )
            conversation = result.scalar_one_or_none()
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="会话不存在"
                )
        
        # 2. 读取最近消息窗口（不包含当前输入）
        recent_history = await _load_recent_history(
            db=db,
            conversation_id=conversation.id,
            limit=RECENT_HISTORY_LIMIT
        )

        # 3. 获取用户画像
        result = await db.execute(
            select(UserProfile).filter(UserProfile.user_id == current_user.id)
        )
        user_profile_obj = result.scalar_one_or_none()
        
        user_profile = None
        if user_profile_obj:
            user_profile = {
                "occupation": user_profile_obj.occupation,
                "learning_goal": user_profile_obj.learning_goal,
                "current_level": user_profile_obj.current_level or {},
                "learning_preference": user_profile_obj.learning_preference or {}
            }
        
        # 4. 获取学习进度（用于Agent决策）
        progress_stats = await progress_service.get_progress_stats(
            user_id=current_user.id,
            db=db
        )

        # 5. 获取短期记忆和会话摘要
        all_short_term_memory = await _load_short_term_memory(session_id)
        short_term_memory = _select_window_external_memory(
            memories=all_short_term_memory,
            recent_history=recent_history,
            limit=SHORT_MEMORY_LIMIT
        )
        conversation_summary = await _load_conversation_summary(conversation, session_id)

        # 6. 构建上下文
        context = {
            "user_id": current_user.id,
            "session_id": session_id,
            "user_profile": user_profile or {},
            "learning_progress": progress_stats or {},
            "recent_history": recent_history,
            "short_term_memory": short_term_memory,
            "conversation_summary": conversation_summary
        }

        # 7. 保存用户消息
        user_message = Message(
            conversation_id=conversation.id,
            user_id=current_user.id,
            role=MessageRole.USER,
            content=request.message,
            extra_data={}
        )
        db.add(user_message)

        # 8. 使用Multi-Agent编排器处理（智能路由）
        result = await agent_orchestrator.process(
            user_input=request.message,
            context=context
        )

        # 9. 保存助手消息
        assistant_message = Message(
            conversation_id=conversation.id,
            user_id=current_user.id,
            role=MessageRole.ASSISTANT,
            content=result["answer"],
            extra_data={
                "sources": result.get("sources", []),
                "confidence": result.get("confidence", 0.0),
                "agent": result.get("agent", "Unknown"),
                "intent": result.get("orchestrator", {}).get("intent", "unknown")
            }
        )
        db.add(assistant_message)

        # 10. 更新会话
        conversation.message_count += 2
        
        await db.commit()
        await db.refresh(assistant_message)
        
        # 11. 写入短期记忆和触发摘要更新（失败不影响主流程）
        try:
            orchestrator_data = result.get("orchestrator", {})
            await _save_short_term_memory(
                user_id=current_user.id,
                session_id=session_id,
                user_message=request.message,
                assistant_message=result["answer"],
                intent=orchestrator_data.get("intent", "unknown"),
                agent=result.get("agent", "Unknown")
            )
        except Exception as e:
            app_logger.warning(f"写入短期记忆失败: {e}")

        try:
            if conversation.message_count > 0 and conversation.message_count % SUMMARY_TRIGGER_INTERVAL == 0:
                await _trigger_summary_update(
                    conversation_id=conversation.id,
                    session_id=session_id,
                    force_fallback=(conversation.summary is None)
                )
        except Exception as e:
            app_logger.warning(f"触发会话摘要更新任务失败: {e}")

        # 12. 异步更新用户画像和学习进度（在后台执行，不阻塞响应）
        try:
            from app.tasks.async_tasks import (
                update_user_profile_from_conversation,
                update_learning_progress_from_conversation
            )

            # 触发学习进度更新
            update_learning_progress_from_conversation.delay(
                user_id=current_user.id,
                user_message=request.message,
                assistant_response=result["answer"],
                conversation_id=conversation.id
            )
            app_logger.info(f"已触发异步学习进度更新任务")

            # 如果对话超过5轮，触发画像更新
            if conversation.message_count >= 10:
                update_user_profile_from_conversation.delay(
                    user_id=current_user.id,
                    conversation_id=conversation.id
                )
                app_logger.info(f"已触发异步画像更新任务")
        except Exception as e:
            app_logger.warning(f"触发异步任务失败: {e}")
        
        app_logger.info(f"用户 {current_user.username} 完成对话，会话ID: {session_id}")
        
        # 13. 构建响应
        return ChatResponse(
            message=result["answer"],
            session_id=session_id,
            sources=[Source(**s) for s in result.get("sources", [])],
            confidence=result.get("confidence", 0.0),
            message_id=assistant_message.id,
            created_at=assistant_message.created_at
        )
        
    except Exception as e:
        app_logger.error(f"对话处理失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对话处理失败: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    对话接口（流式）

    流式返回消息，支持Multi-Agent编排的真正流式处理
    """

    async def generate_stream():
        full_answer = ""
        agent_name = "Unknown"
        intent = "unknown"
        sources = []
        confidence = 0.0

        try:
            # 1. 获取或创建会话
            session_id = request.session_id
            if not session_id:
                session_id = str(uuid.uuid4())
                conversation = Conversation(
                    user_id=current_user.id,
                    session_id=session_id,
                    started_at=datetime.utcnow(),
                    message_count=0
                )
                db.add(conversation)
                await db.flush()
            else:
                result = await db.execute(
                    select(Conversation).filter(
                        Conversation.session_id == session_id,
                        Conversation.user_id == current_user.id
                    )
                )
                conversation = result.scalar_one_or_none()
                if not conversation:
                    yield f"data: {json.dumps({'error': '会话不存在'})}\n\n"
                    return

            # 2. 读取最近消息窗口（不包含当前输入）
            recent_history = await _load_recent_history(
                db=db,
                conversation_id=conversation.id,
                limit=RECENT_HISTORY_LIMIT
            )

            # 3. 获取用户画像
            result = await db.execute(
                select(UserProfile).filter(UserProfile.user_id == current_user.id)
            )
            user_profile_obj = result.scalar_one_or_none()

            user_profile = None
            if user_profile_obj:
                user_profile = {
                    "occupation": user_profile_obj.occupation,
                    "learning_goal": user_profile_obj.learning_goal,
                    "current_level": user_profile_obj.current_level or {},
                    "learning_preference": user_profile_obj.learning_preference or {}
                }

            # 4. 获取学习进度（用于Agent决策）
            progress_stats = await progress_service.get_progress_stats(
                user_id=current_user.id,
                db=db
            )

            # 5. 获取短期记忆和会话摘要
            all_short_term_memory = await _load_short_term_memory(session_id)
            short_term_memory = _select_window_external_memory(
                memories=all_short_term_memory,
                recent_history=recent_history,
                limit=SHORT_MEMORY_LIMIT
            )
            conversation_summary = await _load_conversation_summary(conversation, session_id)

            # 6. 构建上下文
            context = {
                "user_id": current_user.id,
                "session_id": session_id,
                "user_profile": user_profile or {},
                "learning_progress": progress_stats or {},
                "recent_history": recent_history,
                "short_term_memory": short_term_memory,
                "conversation_summary": conversation_summary
            }

            # 6.5 保存用户消息
            user_message = Message(
                conversation_id=conversation.id,
                user_id=current_user.id,
                role=MessageRole.USER,
                content=request.message,
                extra_data={}
            )
            db.add(user_message)
            await db.flush()

            # 7. 发送会话ID
            yield f"data: {json.dumps({'session_id': session_id})}\n\n"
            await asyncio.sleep(0.05)  # 50ms 延迟确保事件立即发送

            # 8. 发送处理中状态
            yield f"data: {json.dumps({'type': 'status', 'status': 'processing'})}\n\n"
            await asyncio.sleep(0.05)  # 50ms 延迟确保事件立即发送

            # 9. 使用Multi-Agent编排器流式处理
            async for chunk in agent_orchestrator.process_stream(
                user_input=request.message,
                context=context
            ):
                chunk_type = chunk.get("type")

                if chunk_type == "status":
                    # 状态信息（thinking, retrieving, generating 等）
                    yield f"data: {json.dumps(chunk)}\n\n"

                elif chunk_type == "orchestrator":
                    # 编排器信息
                    agent_name = chunk.get("selected_agent", "Unknown")
                    intent = chunk.get("intent", "unknown")
                    yield f"data: {json.dumps({'type': 'agent', 'agent': agent_name, 'intent': intent})}\n\n"

                elif chunk_type == "agent":
                    # Agent 信息
                    agent_name = chunk.get("agent", agent_name)
                    yield f"data: {json.dumps(chunk)}\n\n"

                elif chunk_type == "metadata":
                    # 元数据（来源、置信度等）
                    sources = chunk.get("sources", [])
                    confidence = chunk.get("confidence", 0.0)
                    if chunk.get("agent"):
                        agent_name = chunk.get("agent")
                    yield f"data: {json.dumps(chunk)}\n\n"

                elif chunk_type == "answer":
                    # 答案片段
                    content = chunk.get("content", "")
                    full_answer += content
                    yield f"data: {json.dumps(chunk)}\n\n"

                elif chunk_type == "error":
                    # 错误信息
                    yield f"data: {json.dumps(chunk)}\n\n"

            # 10. 保存助手消息
            if full_answer:
                assistant_message = Message(
                    conversation_id=conversation.id,
                    user_id=current_user.id,
                    role=MessageRole.ASSISTANT,
                    content=full_answer,
                    extra_data={
                        "sources": sources,
                        "confidence": confidence,
                        "agent": agent_name,
                        "intent": intent
                    }
                )
                db.add(assistant_message)

                # 11. 更新会话
                conversation.message_count += 2
                await db.commit()

                # 12. 写入短期记忆和触发摘要更新（失败不影响主流程）
                try:
                    await _save_short_term_memory(
                        user_id=current_user.id,
                        session_id=session_id,
                        user_message=request.message,
                        assistant_message=full_answer,
                        intent=intent,
                        agent=agent_name
                    )
                except Exception as e:
                    app_logger.warning(f"写入短期记忆失败: {e}")

                try:
                    if conversation.message_count > 0 and conversation.message_count % SUMMARY_TRIGGER_INTERVAL == 0:
                        await _trigger_summary_update(
                            conversation_id=conversation.id,
                            session_id=session_id,
                            force_fallback=(conversation.summary is None)
                        )
                except Exception as e:
                    app_logger.warning(f"触发会话摘要更新任务失败: {e}")

                # 13. 异步更新学习进度
                try:
                    from app.tasks.async_tasks import update_learning_progress_from_conversation
                    update_learning_progress_from_conversation.delay(
                        user_id=current_user.id,
                        user_message=request.message,
                        assistant_response=full_answer,
                        conversation_id=conversation.id
                    )
                except Exception as e:
                    app_logger.warning(f"触发学习进度更新任务失败: {e}")

            app_logger.info(f"用户 {current_user.username} 完成流式对话，使用Agent: {agent_name}")

        except Exception as e:
            app_logger.error(f"流式对话失败: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        }
    )


@router.get("/sessions")
async def get_chat_sessions(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的对话会话列表
    """
    result = await db.execute(
        select(Conversation).filter(
            Conversation.user_id == current_user.id
        ).order_by(
            Conversation.started_at.desc()
        ).limit(limit).offset(offset)
    )
    conversations = result.scalars().all()
    
    sessions = []
    for conv in conversations:
        # 获取第一条消息作为标题
        first_msg_result = await db.execute(
            select(Message).filter(
                Message.conversation_id == conv.id,
                Message.role == MessageRole.USER
            ).order_by(Message.created_at).limit(1)
        )
        first_msg = first_msg_result.scalar_one_or_none()
        title = first_msg.content[:30] if first_msg else "新对话"
        
        sessions.append({
            "id": conv.session_id,
            "title": title,
            "message_count": conv.message_count,
            "created_at": conv.started_at.isoformat() if conv.started_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None
        })
    
    return {"sessions": sessions, "total": len(sessions)}


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户的某个会话（级联删除消息）
    """
    result = await db.execute(
        select(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    await db.delete(conversation)
    await db.commit()

    app_logger.info(
        f"用户 {current_user.username} 删除会话成功: session_id={session_id}, "
        f"conversation_id={conversation.id}"
    )
    return {"message": "会话已删除", "session_id": session_id}


@router.get("/history/{session_id}", response_model=ChatHistory)
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话历史
    """
    # 查找会话
    result = await db.execute(
        select(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 查找消息
    result = await db.execute(
        select(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    # 构建响应
    return ChatHistory(
        session_id=session_id,
        messages=[
            {"role": msg.role.value, "content": msg.content, "created_at": msg.created_at.isoformat()}
            for msg in messages
        ],
        created_at=conversation.started_at,
        message_count=conversation.message_count
    )
