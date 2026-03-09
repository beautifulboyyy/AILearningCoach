"""
Celery异步任务
"""
from celery_app import celery_app
from app.db.session import async_session_maker
from app.ai.memory.manager import memory_manager
from app.services.progress_service import progress_service
from app.utils.logger import app_logger
import asyncio


def run_async(coro):
    """运行异步函数的辅助函数"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@celery_app.task(name="app.tasks.async_tasks.update_user_profile_from_conversation")
def update_user_profile_from_conversation(user_id: int, conversation_id: int):
    """
    从对话中提取信息并更新用户画像
    
    Args:
        user_id: 用户ID
        conversation_id: 会话ID
    """
    async def _update():
        try:
            async with async_session_maker() as db:
                from app.services.profile_service import profile_service
                from app.models.conversation import Conversation, Message
                from sqlalchemy import select
                
                # 获取会话的所有消息
                result = await db.execute(
                    select(Message).filter(
                        Message.conversation_id == conversation_id
                    ).order_by(Message.created_at)
                )
                messages = result.scalars().all()
                
                # 构建对话文本
                conversation_text = "\n".join([
                    f"{msg.role.value}: {msg.content}"
                    for msg in messages
                ])
                
                # 生成/更新画像
                await profile_service.generate_profile_from_conversation(
                    conversation_text=conversation_text,
                    user_id=user_id,
                    db=db
                )
                
                app_logger.info(f"✅ 已从对话更新用户画像: user_id={user_id}")
                
        except Exception as e:
            app_logger.error(f"❌ 更新用户画像失败: {e}")
            raise
    
    return run_async(_update())


@celery_app.task(name="app.tasks.async_tasks.generate_monthly_report")
def generate_monthly_report(user_id: int):
    """
    生成月报
    
    Args:
        user_id: 用户ID
    """
    async def _generate():
        try:
            async with async_session_maker() as db:
                report = await progress_service.generate_monthly_report(
                    user_id=user_id,
                    db=db
                )
                
                # 这里应该保存报告或发送邮件
                app_logger.info(f"✅ 月报生成完成: user_id={user_id}")
                return report
                
        except Exception as e:
            app_logger.error(f"❌ 生成月报失败: {e}")
            raise
    
    return run_async(_generate())


@celery_app.task(name="app.tasks.async_tasks.save_important_memory")
def save_important_memory(user_id: int, content: str, importance_score: float):
    """
    异步保存重要记忆到长期记忆

    Args:
        user_id: 用户ID
        content: 记忆内容
        importance_score: 重要性评分
    """
    async def _save():
        try:
            async with async_session_maker() as db:
                memory = await memory_manager.save_long_term_memory(
                    user_id=user_id,
                    content=content,
                    importance_score=importance_score,
                    db=db
                )

                app_logger.info(f"✅ 异步保存长期记忆: memory_id={memory.id}")
                return memory.id

        except Exception as e:
            app_logger.error(f"❌ 保存长期记忆失败: {e}")
            raise

    return run_async(_save())


@celery_app.task(name="app.tasks.async_tasks.update_learning_progress_from_conversation")
def update_learning_progress_from_conversation(
    user_id: int,
    user_message: str,
    assistant_response: str,
    conversation_id: int
):
    """
    根据对话内容自动更新学习进度

    Args:
        user_id: 用户ID
        user_message: 用户消息
        assistant_response: AI回复
        conversation_id: 会话ID
    """
    async def _update():
        try:
            async with async_session_maker() as db:
                from app.services.progress_sync_service import progress_sync_service
                from app.models.progress import ProgressTriggerType

                # 1. 从对话内容识别模块
                result = await progress_sync_service.identify_module_from_content(
                    content=user_message,
                    user_id=user_id,
                    db=db
                )

                if not result:
                    app_logger.debug(f"未能从对话中识别出学习模块: user_id={user_id}")
                    return None

                module_key, confidence = result

                # 2. 只有置信度足够高时才更新进度
                if confidence < 0.3:
                    app_logger.debug(f"模块识别置信度过低: {confidence}")
                    return None

                # 3. 计算进度增量
                delta = await progress_sync_service.calculate_conversation_progress_delta(
                    content=user_message,
                    response=assistant_response
                )

                # 根据置信度调整增量
                adjusted_delta = delta * confidence

                # 4. 更新进度
                progress = await progress_sync_service.update_module_progress(
                    user_id=user_id,
                    module_key=module_key,
                    completion_delta=adjusted_delta,
                    trigger_type=ProgressTriggerType.CONVERSATION,
                    trigger_source=f"conversation:{conversation_id}",
                    trigger_detail=f"问题: {user_message[:100]}...",
                    db=db
                )

                if progress:
                    app_logger.info(
                        f"✅ 对话触发进度更新: user_id={user_id}, module={module_key}, "
                        f"delta=+{adjusted_delta:.1f}%"
                    )
                    return {
                        "module_key": module_key,
                        "delta": adjusted_delta,
                        "new_percentage": progress.completion_percentage
                    }

                return None

        except Exception as e:
            app_logger.error(f"❌ 对话触发进度更新失败: {e}")
            # 不重新抛出异常，因为这是一个非关键任务
            return None

    return run_async(_update())
