"""
学习规划Agent（Planner Agent）
"""
from typing import Dict, Any
from app.ai.agents.base import BaseAgent
from app.ai.agents.message_builder import build_agent_messages
from app.ai.rag.llm import llm
from app.ai.prompts.system_prompts import LEARNING_PLANNER_SYSTEM_PROMPT
from app.utils.logger import app_logger
import json
import re


class PlannerAgent(BaseAgent):
    """
    学习规划Agent
    
    专注于生成和调整学习路径，提供个性化学习建议
    """
    
    def __init__(self):
        super().__init__(
            name="Planner Agent",
            description="学习规划助手，负责生成个性化学习路径和学习建议"
        )
        self.llm = llm
    
    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理学习规划请求
        
        Args:
            user_input: 用户输入
            context: 上下文
        
        Returns:
            规划结果
        """
        try:
            app_logger.info(f"Planner Agent处理规划请求: {user_input[:50]}...")
            
            # 从上下文获取信息
            user_profile = context.get("user_profile", {})
            learning_progress = context.get("learning_progress", {})
            
            # 构建规划Prompt
            profile_info = ""
            if user_profile:
                profile_info = f"""
## 用户背景
- 职业：{user_profile.get('occupation', '未知')}
- 学习目标：{user_profile.get('learning_goal', '未知')}
- 当前水平：{json.dumps(user_profile.get('current_level', {}), ensure_ascii=False)}
"""
            
            progress_info = ""
            if learning_progress:
                completed = learning_progress.get('completed_modules', [])
                if completed:
                    progress_info = f"\n## 已完成模块\n{', '.join(completed)}"
            
            planning_prompt = f"""{LEARNING_PLANNER_SYSTEM_PROMPT}

{profile_info}
{progress_info}

请根据用户的背景、进度和需求，提供学习规划建议。
"""
            messages = build_agent_messages(
                system_prompt=planning_prompt,
                user_input=user_input,
                context=context
            )
            
            # 生成规划建议
            response = await self.llm.generate(
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            return {
                "agent": self.name,
                "type": "learning_plan",
                "answer": response,
                "sources": [],
                "confidence": 0.9,
                "success": True
            }
            
        except Exception as e:
            app_logger.error(f"Planner Agent处理失败: {e}")
            return {
                "agent": self.name,
                "type": "learning_plan",
                "answer": "抱歉，我在制定学习计划时遇到了问题。",
                "sources": [],
                "confidence": 0.0,
                "success": False,
                "error": str(e)
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
        planning_keywords = [
            "规划", "计划", "路径", "学习安排", "怎么学",
            "从哪开始", "先学什么", "推荐", "建议",
            "学习方法", "学习顺序"
        ]
        
        return (
            intent == "learning_planning" or
            any(keyword in user_input for keyword in planning_keywords)
        )


# 全局Planner Agent实例
planner_agent = PlannerAgent()
