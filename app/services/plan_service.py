"""
学习计划服务模块 - 使用 DeepSeek LLM 生成个性化学习计划
"""
from typing import Dict, Any, List, Optional
from app.ai.rag.llm import llm
from app.utils.logger import app_logger
import json


class PlanService:
    """学习计划服务 - 生成个性化学习计划"""

    def __init__(self):
        self.llm = llm

    async def generate_plan(
        self,
        user_background: Dict[str, Any],
        target: str,
        available_hours_per_week: int = 10
    ) -> Dict[str, Any]:
        """
        生成学习计划

        Args:
            user_background: 用户背景信息
            target: 学习目标
            available_hours_per_week: 每周可用学习时间（小时）

        Returns:
            学习计划字典
        """
        system_prompt = """你是一个专业的AI学习规划专家。根据学习者的背景和目标，生成一个详细且可执行的学习计划。

输出必须是严格的 JSON 格式，结构如下：
{
  "title": "计划标题",
  "description": "计划整体描述",
  "estimated_weeks": 预计完成周数,
  "milestones": [
    {
      "title": "里程碑标题",
      "description": "里程碑描述",
      "week_start": 开始周数,
      "week_end": 结束周数,
      "tasks": [
        {
          "title": "任务标题",
          "content": "任务详细内容",
          "estimated_hours": 预计学习时长,
          "resources": ["推荐资源1", "推荐资源2"]
        }
      ]
    }
  ],
  "prerequisites": ["前置知识1", "前置知识2"],
  "tips": ["学习建议1", "学习建议2"]
}

请确保：
1. 计划具有可执行性，任务划分合理
2. 考虑学习者的背景和每周可用时间
3. 里程碑之间有清晰的递进关系
4. 每个任务都有具体的学习内容和预计时长
5. 只输出JSON，不要其他内容"""

        user_message = f"""用户背景：
{json.dumps(user_background, ensure_ascii=False, indent=2)}

学习目标：{target}

每周可用学习时间：{available_hours_per_week}小时

请为该用户生成一个详细的学习计划。"""

        try:
            response = await self.llm.chat(
                user_message=user_message,
                system_message=system_prompt,
                temperature=0.5,
                max_tokens=3000
            )

            # 尝试解析JSON
            # 处理可能的markdown代码块
            content = response.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            plan = json.loads(content)
            app_logger.info(f"成功生成学习计划: {plan.get('title', '未命名计划')}")
            return plan

        except json.JSONDecodeError as e:
            app_logger.error(f"解析学习计划JSON失败: {e}")
            # 返回基础结构
            return {
                "title": f"{target}学习计划",
                "description": "自动生成的学习计划",
                "estimated_weeks": 8,
                "milestones": [
                    {
                        "title": "基础阶段",
                        "description": "学习基础知识",
                        "week_start": 1,
                        "week_end": 4,
                        "tasks": [
                            {
                                "title": "学习基础概念",
                                "content": f"系统学习{target}的基础概念和原理",
                                "estimated_hours": 20,
                                "resources": []
                            }
                        ]
                    }
                ],
                "prerequisites": [],
                "tips": ["建议每天保持学习", "多动手实践"]
            }
        except Exception as e:
            app_logger.error(f"生成学习计划失败: {e}")
            raise

    async def refine_plan(
        self,
        current_plan: Dict[str, Any],
        feedback: str
    ) -> Dict[str, Any]:
        """
        根据反馈优化学习计划

        Args:
            current_plan: 当前计划
            feedback: 用户反馈

        Returns:
            优化后的计划
        """
        system_prompt = """你是一个专业的AI学习规划专家。请根据用户的反馈，优化现有的学习计划。

保持输出的JSON格式与原计划一致，只对需要调整的部分进行修改。
只输出JSON，不要其他内容。"""

        user_message = f"""当前学习计划：
{json.dumps(current_plan, ensure_ascii=False, indent=2)}

用户反馈：{feedback}

请根据反馈优化这个学习计划。"""

        try:
            response = await self.llm.chat(
                user_message=user_message,
                system_message=system_prompt,
                temperature=0.5,
                max_tokens=3000
            )

            content = response.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            refined_plan = json.loads(content)
            app_logger.info("成功优化学习计划")
            return refined_plan

        except Exception as e:
            app_logger.error(f"优化学习计划失败: {e}")
            return current_plan


# 全局计划服务实例
plan_service = PlanService()
