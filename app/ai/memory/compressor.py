"""
记忆压缩模块
"""
from typing import List, Dict, Any
from app.ai.rag.llm import llm
from app.utils.logger import app_logger


class MemoryCompressor:
    """记忆压缩器"""
    
    def __init__(self):
        self.llm = llm
    
    async def compress_conversation(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500
    ) -> str:
        """
        压缩对话历史为摘要
        
        将完整的对话历史压缩为结构化的摘要，大幅降低Token使用
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            max_tokens: 压缩后的最大token数
        
        Returns:
            压缩后的摘要文本
        """
        if not messages:
            return ""
        
        # 构建对话文本
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])
        
        # 压缩Prompt
        compress_prompt = f"""请将以下对话压缩为简洁的摘要，保留关键信息。

对话内容：
{conversation_text}

请提取和总结：
1. 用户提出的主要问题和关注点
2. 讨论的核心技术主题
3. 用户的学习进展或困难
4. 重要的决策或结论

输出格式：简洁的结构化摘要，不超过{max_tokens // 2}字。
"""
        
        try:
            summary = await self.llm.generate(
                messages=[{"role": "user", "content": compress_prompt}],
                temperature=0.3,
                max_tokens=max_tokens
            )
            
            app_logger.info(
                f"对话压缩完成: 原始={len(conversation_text)}字符, "
                f"压缩后={len(summary)}字符, "
                f"压缩率={len(summary)/len(conversation_text)*100:.1f}%"
            )
            
            return summary
            
        except Exception as e:
            app_logger.error(f"对话压缩失败: {e}")
            # 降级：返回最近几条消息的简单拼接
            recent_messages = messages[-3:]
            return "\n".join([f"{m['role']}: {m['content'][:100]}" for m in recent_messages])
    
    async def extract_key_information(
        self,
        conversation_text: str
    ) -> Dict[str, Any]:
        """
        从对话中提取关键信息
        
        Args:
            conversation_text: 对话文本
        
        Returns:
            提取的结构化信息
        """
        extraction_prompt = f"""请从以下对话中提取关键信息，以JSON格式返回。

对话内容：
{conversation_text}

请提取以下信息（如果对话中没有提到，设为null）：
1. learning_progress: 学习进度更新（如"开始学习RAG"、"完成Prompt工程"）
2. difficulties: 遇到的困难点（列表）
3. preferences: 学习偏好变化（如"喜欢实战案例"、"偏好详细讲解"）
4. technical_updates: 技术背景更新（如"会用FastAPI了"、"学会了向量数据库"）
5. questions_topics: 提问的主题分类（列表）
6. importance_score: 这段对话的重要性（0-1之间的浮点数）

只返回JSON格式，不要有其他文字。
"""
        
        try:
            response = await self.llm.generate(
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            # 解析JSON
            import json
            import re
            
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()
            
            extracted_info = json.loads(json_str)
            
            app_logger.info(f"关键信息提取完成: {len(extracted_info)} 个字段")
            return extracted_info
            
        except Exception as e:
            app_logger.error(f"信息提取失败: {e}")
            return {
                "learning_progress": None,
                "difficulties": [],
                "preferences": None,
                "technical_updates": None,
                "questions_topics": [],
                "importance_score": 0.5
            }
    
    async def compress_memory_summary(
        self,
        profile: Dict[str, Any],
        recent_memories: List[str]
    ) -> str:
        """
        将用户画像和最近记忆压缩为简洁摘要
        
        这是记忆系统的核心优化：将5000+ tokens压缩到300-500 tokens
        
        Args:
            profile: 用户画像字典
            recent_memories: 最近的记忆列表
        
        Returns:
            压缩的记忆摘要
        """
        # 构建画像摘要
        profile_parts = []
        
        if profile.get("occupation"):
            profile_parts.append(f"职业：{profile['occupation']}")
        
        if profile.get("learning_goal"):
            goal_map = {
                "job_hunting": "求职准备",
                "project": "项目实战",
                "systematic_learning": "系统学习"
            }
            profile_parts.append(f"目标：{goal_map.get(profile['learning_goal'], profile['learning_goal'])}")
        
        if profile.get("current_level"):
            levels = []
            for module, level in profile["current_level"].items():
                if level != "not_started":
                    levels.append(f"{module}({level})")
            if levels:
                profile_parts.append(f"水平：{', '.join(levels[:3])}")
        
        profile_summary = "；".join(profile_parts)
        
        # 最近记忆摘要（只保留最重要的3条）
        memory_summary = ""
        if recent_memories:
            memory_summary = "\n最近学习：" + "；".join(recent_memories[:3])
        
        # 组合压缩摘要
        compressed = f"用户画像：{profile_summary}{memory_summary}"
        
        app_logger.info(f"记忆摘要生成: {len(compressed)} 字符")
        
        return compressed


# 全局压缩器实例
memory_compressor = MemoryCompressor()
