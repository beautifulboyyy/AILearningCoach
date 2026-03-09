"""
进度分析Agent（Analyst Agent）
"""
from typing import Dict, Any
from app.ai.agents.base import BaseAgent
from app.ai.rag.llm import llm
from app.ai.prompts.system_prompts import PROGRESS_ANALYST_SYSTEM_PROMPT
from app.utils.logger import app_logger


class AnalystAgent(BaseAgent):
    """
    进度分析Agent
    
    专注于分析学习数据，生成学习报告和建议
    """
    
    def __init__(self):
        super().__init__(
            name="Analyst Agent",
            description="进度分析助手，分析学习数据并生成洞察和建议"
        )
        self.llm = llm
    
    async def process(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理进度分析请求
        
        Args:
            user_input: 用户输入
            context: 上下文
        
        Returns:
            分析结果
        """
        try:
            app_logger.info(f"Analyst Agent处理分析请求: {user_input[:50]}...")
            
            # 从上下文获取学习数据
            learning_progress = context.get("learning_progress", {})
            recent_activities = context.get("recent_activities", [])
            
            # 构建分析Prompt
            progress_info = f"""
## 学习数据
- 总模块数：{learning_progress.get('total_modules', 0)}
- 已完成：{learning_progress.get('completed_modules', 0)}
- 进行中：{learning_progress.get('in_progress_modules', 0)}
- 总体完成度：{learning_progress.get('overall_completion', 0)}%
- 当前模块：{learning_progress.get('current_module', '无')}
"""
            
            activities_info = ""
            if recent_activities:
                activities_info = f"\n## 最近活动\n" + "\n".join(recent_activities[:5])
            
            analyst_prompt = f"""{PROGRESS_ANALYST_SYSTEM_PROMPT}

{progress_info}
{activities_info}

## 用户请求
{user_input}

请分析学习数据，提供洞察和建议。
"""
            
            # 生成分析报告
            response = await self.llm.generate(
                messages=[{"role": "user", "content": analyst_prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            
            return {
                "agent": self.name,
                "type": "progress_analysis",
                "answer": response,
                "sources": [],
                "confidence": 0.9,
                "success": True
            }
            
        except Exception as e:
            app_logger.error(f"Analyst Agent处理失败: {e}")
            return {
                "agent": self.name,
                "type": "progress_analysis",
                "answer": "抱歉，我在分析你的学习数据时遇到了问题。",
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
        analysis_keywords = [
            "进度", "报告", "总结", "分析", "统计",
            "学了多少", "完成情况", "学习效果",
            "周报", "月报", "复习"
        ]
        
        return (
            intent == "progress_inquiry" or
            any(keyword in user_input for keyword in analysis_keywords)
        )


# 全局Analyst Agent实例
analyst_agent = AnalystAgent()
