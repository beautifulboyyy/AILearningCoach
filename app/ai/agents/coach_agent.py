"""
项目指导Agent（Coach Agent）
"""
from typing import Dict, Any
from app.ai.agents.base import BaseAgent
from app.ai.rag.llm import llm
from app.ai.prompts.system_prompts import PROJECT_COACH_SYSTEM_PROMPT
from app.utils.logger import app_logger


class CoachAgent(BaseAgent):
    """
    项目指导Agent
    
    专注于项目实战指导，提供代码审查和问题诊断
    """
    
    def __init__(self):
        super().__init__(
            name="Coach Agent",
            description="项目指导助手，帮助完成实战项目，提供代码审查和问题诊断"
        )
        self.llm = llm
    
    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理项目指导请求
        
        Args:
            user_input: 用户输入
            context: 上下文
        
        Returns:
            指导结果
        """
        try:
            app_logger.info(f"Coach Agent处理项目指导: {user_input[:50]}...")
            
            # 从上下文获取信息
            user_profile = context.get("user_profile", {})
            
            # 构建指导Prompt
            profile_info = ""
            if user_profile:
                profile_info = f"""
## 学习者背景
- 职业：{user_profile.get('occupation', '未知')}
- 技术水平：{user_profile.get('current_level', {})}
"""
            
            coach_prompt = f"""{PROJECT_COACH_SYSTEM_PROMPT}

{profile_info}

## 学习者问题
{user_input}

请提供具体的项目指导建议。
"""
            
            # 生成指导建议
            response = await self.llm.generate(
                messages=[{"role": "user", "content": coach_prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            
            return {
                "agent": self.name,
                "type": "project_coaching",
                "answer": response,
                "sources": [],
                "confidence": 0.85,
                "success": True
            }
            
        except Exception as e:
            app_logger.error(f"Coach Agent处理失败: {e}")
            return {
                "agent": self.name,
                "type": "project_coaching",
                "answer": "抱歉，我在提供项目指导时遇到了问题。",
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
        project_keywords = [
            "项目", "代码", "实现", "bug", "错误", "优化",
            "部署", "架构", "设计", "调试", "审查",
            "为什么报错", "怎么做", "实战"
        ]
        
        return (
            intent == "project_guidance" or
            any(keyword in user_input for keyword in project_keywords)
        )


# 全局Coach Agent实例
coach_agent = CoachAgent()
