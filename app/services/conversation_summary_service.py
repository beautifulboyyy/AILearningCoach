"""
会话摘要服务
"""
from datetime import datetime
from typing import Optional, List, Dict

from sqlalchemy import select

from app.ai.memory.compressor import memory_compressor
from app.db.session import async_session_maker
from app.models.conversation import Conversation, Message
from app.utils.cache import cache_set
from app.utils.logger import app_logger


class ConversationSummaryService:
    """会话摘要更新服务（可供API兜底与Celery复用）"""

    async def update_conversation_summary(
        self,
        conversation_id: int,
        session_id: str,
        message_limit: int = 20
    ) -> Optional[str]:
        """
        更新会话摘要到 PostgreSQL + Redis。
        """
        try:
            async with async_session_maker() as db:
                conversation_result = await db.execute(
                    select(Conversation).filter(Conversation.id == conversation_id)
                )
                conversation = conversation_result.scalar_one_or_none()
                if not conversation:
                    app_logger.warning(f"会话不存在，无法更新摘要: conversation_id={conversation_id}")
                    return None

                message_result = await db.execute(
                    select(Message).filter(
                        Message.conversation_id == conversation_id
                    ).order_by(Message.created_at.desc()).limit(message_limit)
                )
                recent_messages = list(message_result.scalars().all())
                if not recent_messages:
                    return None

                recent_messages.reverse()
                structured_messages: List[Dict[str, str]] = [
                    {"role": msg.role.value, "content": msg.content}
                    for msg in recent_messages
                ]

                summary = await memory_compressor.compress_conversation(
                    messages=structured_messages,
                    max_tokens=600
                )
                if not summary:
                    return None

                conversation.summary = summary
                conversation.summary_updated_at = datetime.utcnow()
                await db.commit()

                summary_key = f"session:{session_id}:summary"
                await cache_set(summary_key, summary, expire=7200)

                app_logger.info(
                    f"✅ 会话摘要更新成功: conversation_id={conversation_id}, summary_length={len(summary)}"
                )
                return summary

        except Exception as e:
            app_logger.error(f"❌ 更新会话摘要失败: {e}")
            return None


conversation_summary_service = ConversationSummaryService()
