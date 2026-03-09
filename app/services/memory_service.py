"""
记忆服务模块 - 从对话中提取和存储用户记忆
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.rag.llm import llm
from app.ai.rag.embeddings import embedding_model
from app.ai.memory.manager import memory_manager
from app.models.memory import Memory, MemoryType
from app.utils.logger import app_logger
import json


class MemoryService:
    """记忆服务 - 从对话中提取关键信息并存储"""

    def __init__(self):
        self.llm = llm
        self.embedding = embedding_model

    async def extract_facts_from_dialogue(self, dialogue: str) -> List[str]:
        """
        从对话中提取关键事实

        Args:
            dialogue: 对话内容

        Returns:
            提取的事实列表
        """
        system_prompt = """你是一个记忆提取助手。从以下对话中提取关于用户的关键事实。
提取的信息应包括但不限于：
- 技术背景和技能水平
- 学习偏好和风格
- 遇到的困难和问题
- 目标和期望
- 已完成的学习内容

请以JSON数组格式输出，每个元素是一个独立的事实。
示例输出：["用户熟悉Python编程", "用户正在学习机器学习", "用户偏好项目驱动学习"]

只输出JSON数组，不要其他内容。"""

        try:
            response = await self.llm.chat(
                user_message=f"对话内容：\n{dialogue}",
                system_message=system_prompt,
                temperature=0.3
            )

            # 解析JSON响应
            facts = json.loads(response)
            if isinstance(facts, list):
                return facts
            return [str(facts)]

        except json.JSONDecodeError:
            # 如果无法解析JSON，按行分割
            lines = response.strip().split('\n')
            return [line.strip('- ').strip() for line in lines if line.strip()]
        except Exception as e:
            app_logger.error(f"提取对话事实失败: {e}")
            return []

    async def extract_and_store_memory(
        self,
        user_id: int,
        dialogue: str,
        db: AsyncSession
    ) -> List[Memory]:
        """
        从对话中提取事实并存储为长期记忆

        Args:
            user_id: 用户ID
            dialogue: 对话内容
            db: 数据库会话

        Returns:
            存储的记忆列表
        """
        # 1. 提取事实
        facts = await self.extract_facts_from_dialogue(dialogue)

        if not facts:
            app_logger.info(f"未从对话中提取到有效事实: user_id={user_id}")
            return []

        # 2. 存储每个事实为长期记忆
        stored_memories = []
        for fact in facts:
            try:
                # 计算重要性分数（基于内容长度和关键词）
                importance = self._calculate_importance(fact)

                # 使用 memory_manager 存储
                memory = await memory_manager.save_long_term_memory(
                    user_id=user_id,
                    content=fact,
                    importance_score=importance,
                    db=db
                )
                stored_memories.append(memory)

            except Exception as e:
                app_logger.error(f"存储记忆失败: {e}")
                continue

        app_logger.info(f"成功存储 {len(stored_memories)} 条记忆: user_id={user_id}")
        return stored_memories

    def _calculate_importance(self, fact: str) -> float:
        """
        计算事实的重要性分数

        Args:
            fact: 事实内容

        Returns:
            重要性分数 (0.0 - 1.0)
        """
        # 基础分数
        score = 0.5

        # 关键词权重
        high_importance_keywords = ['目标', '困难', '问题', '需求', '计划', '擅长', '熟悉']
        medium_importance_keywords = ['学习', '了解', '使用', '接触', '知道']

        for keyword in high_importance_keywords:
            if keyword in fact:
                score += 0.1

        for keyword in medium_importance_keywords:
            if keyword in fact:
                score += 0.05

        # 长度因素（适中长度更重要）
        length = len(fact)
        if 20 <= length <= 100:
            score += 0.1
        elif length > 100:
            score += 0.05

        return min(score, 1.0)

    async def get_relevant_memories(
        self,
        user_id: int,
        query: str,
        db: AsyncSession,
        top_k: int = 5
    ) -> List[Memory]:
        """
        获取与查询相关的记忆

        Args:
            user_id: 用户ID
            query: 查询内容
            db: 数据库会话
            top_k: 返回数量

        Returns:
            相关记忆列表
        """
        return await memory_manager.search_long_term_memory(
            user_id=user_id,
            query=query,
            db=db,
            top_k=top_k
        )


# 全局记忆服务实例
memory_service = MemoryService()
