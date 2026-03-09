"""
对话相关API
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
import json

from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.conversation import Conversation, Message, MessageRole
from app.models.profile import UserProfile
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistory, Source
from app.ai.rag.generator import rag_generator
from app.ai.agents.orchestrator import agent_orchestrator
from app.services.progress_service import progress_service
from app.utils.logger import app_logger

router = APIRouter()


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
        
        # 2. 保存用户消息
        user_message = Message(
            conversation_id=conversation.id,
            user_id=current_user.id,
            role=MessageRole.USER,
            content=request.message,
            extra_data={}
        )
        db.add(user_message)
        
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
        
        # 5. 构建上下文
        context = {
            "user_id": current_user.id,
            "session_id": session_id,
            "user_profile": user_profile,
            "learning_progress": progress_stats
        }
        
        # 6. 使用Multi-Agent编排器处理（智能路由）
        result = await agent_orchestrator.process(
            user_input=request.message,
            context=context
        )
        
        # 7. 保存助手消息
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
        
        # 8. 更新会话
        conversation.message_count += 2
        
        await db.commit()
        await db.refresh(assistant_message)
        
        # 9. 异步更新用户画像和学习进度（在后台执行，不阻塞响应）
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
        
        # 10. 构建响应
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

            # 2. 保存用户消息
            user_message = Message(
                conversation_id=conversation.id,
                user_id=current_user.id,
                role=MessageRole.USER,
                content=request.message,
                extra_data={}
            )
            db.add(user_message)
            await db.flush()

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

            # 5. 构建上下文
            context = {
                "user_id": current_user.id,
                "session_id": session_id,
                "user_profile": user_profile,
                "learning_progress": progress_stats
            }

            # 6. 发送会话ID
            yield f"data: {json.dumps({'session_id': session_id})}\n\n"
            await asyncio.sleep(0.05)  # 50ms 延迟确保事件立即发送

            # 7. 发送处理中状态
            yield f"data: {json.dumps({'type': 'status', 'status': 'processing'})}\n\n"
            await asyncio.sleep(0.05)  # 50ms 延迟确保事件立即发送

            # 8. 使用Multi-Agent编排器流式处理
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

            # 9. 保存助手消息
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

                # 10. 更新会话
                conversation.message_count += 2
                await db.commit()

                # 11. 异步更新学习进度
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
