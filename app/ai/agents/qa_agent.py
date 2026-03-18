"""
问答Agent（QA Agent）
"""
from typing import Dict, Any, AsyncGenerator
from app.ai.agents.base import BaseAgent
from app.ai.agents.message_builder import normalize_history, build_context_note
from app.ai.rag.generator import rag_generator
from app.utils.logger import app_logger


class QAAgent(BaseAgent):
    """
    问答Agent

    专注于回答技术问题，调用RAG系统检索知识库
    """

    def __init__(self):
        super().__init__(
            name="QA Agent",
            description="技术问答助手，专门回答LLM应用开发相关的技术问题"
        )
        self.rag = rag_generator

    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理技术问答

        Args:
            user_input: 用户问题
            context: 上下文（包含user_profile等）

        Returns:
            答案结果
        """
        try:
            app_logger.info(f"QA Agent处理问题: {user_input[:50]}...")

            # 从上下文中获取用户画像
            user_profile = context.get("user_profile")
            recent_history = normalize_history(context.get("recent_history"))
            context_note = build_context_note(context)

            # 调用RAG系统生成答案
            result = await self.rag.generate(
                query=user_input,
                user_profile=user_profile,
                conversation_messages=recent_history,
                extra_context=context_note,
                top_k=3,
                temperature=0.7
            )

            return {
                "agent": self.name,
                "type": "technical_qa",
                "answer": result["answer"],
                "sources": result["sources"],
                "confidence": result["confidence"],
                "success": True
            }

        except Exception as e:
            app_logger.error(f"QA Agent处理失败: {e}")
            return {
                "agent": self.name,
                "type": "technical_qa",
                "answer": f"抱歉，我在处理你的问题时遇到了错误。请稍后重试。",
                "sources": [],
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }

    async def process_stream(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式处理技术问答

        Args:
            user_input: 用户问题
            context: 上下文

        Yields:
            答案片段
        """
        try:
            app_logger.info(f"QA Agent 流式处理问题: {user_input[:50]}...")

            # 从上下文中获取用户画像
            user_profile = context.get("user_profile")
            recent_history = normalize_history(context.get("recent_history"))
            context_note = build_context_note(context)

            import asyncio

            # 发送 Agent 信息
            yield {
                "type": "agent",
                "agent": self.name,
                "agent_type": "technical_qa"
            }
            await asyncio.sleep(0.05)  # 50ms 延迟确保事件立即发送

            # 使用 RAG 流式生成
            async for chunk in self.rag.generate_stream(
                query=user_input,
                user_profile=user_profile,
                conversation_messages=recent_history,
                extra_context=context_note,
                top_k=3,
                temperature=0.7
            ):
                yield chunk

            app_logger.info("QA Agent 流式处理完成")

        except Exception as e:
            app_logger.error(f"QA Agent 流式处理失败: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "agent": self.name
            }
    
    def can_handle(self, user_input: str, intent: str) -> bool:
        """
        判断是否可以处理该输入
        
        Args:
            user_input: 用户输入
            intent: 意图识别结果
        
        Returns:
            是否可以处理
        """
        # QA Agent处理技术问题
        technical_keywords = [
            "什么是", "如何", "怎么", "为什么", "原理", 
            "区别", "对比", "实现", "用法", "配置",
            "RAG", "Agent", "Prompt", "向量", "检索"
        ]
        
        return (
            intent == "technical_question" or
            any(keyword in user_input for keyword in technical_keywords)
        )


# 全局QA Agent实例
qa_agent = QAAgent()
