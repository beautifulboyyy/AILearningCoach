"""
学习路径服务
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.learning_path import LearningPath, PathStatus
from app.models.profile import UserProfile
from app.ai.rag.llm import llm
from app.ai.prompts.system_prompts import LEARNING_PLANNER_SYSTEM_PROMPT
from app.utils.logger import app_logger
import json
import re


class LearningPathService:
    """学习路径服务"""

    GOAL_FOCUS = {
        "job_hunting": ["Prompt工程", "RAG系统", "Agent开发", "综合项目"],
        "project": ["Prompt工程", "Function Calling", "RAG系统", "Agent开发", "综合项目"],
        "systematic_learning": ["Prompt工程", "Function Calling", "RAG系统", "Agent开发", "MCP", "综合项目"],
        "skill_improvement": ["Prompt工程", "RAG系统", "Agent开发", "综合项目"],
        "hobby_learning": ["Prompt工程", "RAG系统", "综合项目"],
        "exam_preparation": ["Prompt工程", "Function Calling", "RAG系统", "Agent开发"],
    }

    MODULE_LIBRARY = {
        "Prompt工程": ["讲03-Prompt基础", "讲04-中级Prompt", "讲05-高级Prompt"],
        "Function Calling": ["讲06-Prompt实战", "讲07-Prompt工程化"],
        "RAG系统": ["讲08-Embedding", "讲09-向量数据库", "讲10-检索", "讲11-RAG基础", "讲12-RAG进阶"],
        "Agent开发": ["讲15-Agent基础", "讲16-Tool Use", "讲17-多Agent"],
        "MCP": ["讲18-Agent框架", "讲19-Agent实战"],
        "综合项目": ["讲20-综合项目"],
    }
    
    async def generate_learning_path(
        self,
        user_id: int,
        learning_goal: str,
        available_hours: int,
        db: AsyncSession,
        prior_knowledge: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> LearningPath:
        """
        生成个性化学习路径
        
        Args:
            user_id: 用户ID
            learning_goal: 学习目标
            available_hours: 每周可用时间
            db: 数据库会话
            prior_knowledge: 已有知识
            preferences: 学习偏好
        
        Returns:
            学习路径对象
        """
        try:
            # 获取用户画像
            result = await db.execute(
                select(UserProfile).filter(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            
            # 1) 先构建规则化计划骨架（保证不会固定死模板）
            base_plan = self._build_rule_based_plan(
                learning_goal=learning_goal,
                available_hours=available_hours,
                prior_knowledge=prior_knowledge,
                profile=profile
            )

            # 2) 使用LLM在骨架上润色（失败则回退骨架）
            profile_info = ""
            if profile:
                profile_info = (
                    f"职业：{profile.occupation or '未知'}；"
                    f"技术背景：{json.dumps(profile.technical_background or {}, ensure_ascii=False)}；"
                    f"当前水平：{json.dumps(profile.current_level or {}, ensure_ascii=False)}"
                )

            planning_prompt = f"""请基于下面学习路径骨架，输出更自然且可执行的学习路径JSON。
要求：
1. 保留 phases 的先后逻辑，不要删除核心阶段
2. 可微调阶段标题/目标/模块细节
3. 输出必须是 JSON，字段保持 title/description/phases

学习目标：{learning_goal}
每周可用时长：{available_hours}小时
用户画像：{profile_info or "未知"}
已有知识：{json.dumps(prior_knowledge or {}, ensure_ascii=False)}

骨架JSON：
{json.dumps(base_plan, ensure_ascii=False)}
"""

            learning_plan = base_plan
            try:
                response = await llm.generate(
                    messages=[{"role": "user", "content": planning_prompt}],
                    temperature=0.6,
                    max_tokens=1200
                )
                parsed_plan = self._parse_learning_plan(response)
                if parsed_plan and parsed_plan.get("phases"):
                    learning_plan = parsed_plan
            except Exception as llm_error:
                app_logger.warning(f"LLM润色学习路径失败，使用规则化结果: {llm_error}")
            
            # 创建学习路径
            learning_path = LearningPath(
                user_id=user_id,
                title=learning_plan.get("title", "我的学习路径"),
                description=learning_plan.get("description", ""),
                phases=learning_plan.get("phases", []),
                status=PathStatus.ACTIVE
            )
            
            db.add(learning_path)
            await db.commit()
            await db.refresh(learning_path)

            # 同步模块到 PathModule 表
            from app.services.progress_sync_service import progress_sync_service
            await progress_sync_service.sync_path_modules(learning_path, db)

            app_logger.info(f"生成学习路径: user_id={user_id}, path_id={learning_path.id}")
            return learning_path
            
        except Exception as e:
            app_logger.error(f"生成学习路径失败: {e}")
            raise

    def _parse_learning_plan(self, response: str) -> Optional[Dict[str, Any]]:
        """
        尝试从LLM响应中解析学习路径JSON。
        """
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(response.strip())
        except Exception:
            return None

    def _build_rule_based_plan(
        self,
        learning_goal: str,
        available_hours: int,
        prior_knowledge: Optional[Dict[str, Any]] = None,
        profile: Optional[UserProfile] = None
    ) -> Dict[str, Any]:
        """
        基于目标和可用时长生成动态学习路径骨架。
        """
        goal_key = learning_goal if learning_goal in self.GOAL_FOCUS else "systematic_learning"
        focus_topics = self.GOAL_FOCUS[goal_key]

        # 根据每周时长动态设置总周数
        if available_hours <= 6:
            total_weeks = 12
        elif available_hours <= 10:
            total_weeks = 10
        elif available_hours <= 16:
            total_weeks = 8
        else:
            total_weeks = 6

        phase_count = min(max(3, len(focus_topics)), 5)
        topics_for_plan = focus_topics[:phase_count]

        phases: List[Dict[str, Any]] = []
        start_week = 1
        weeks_per_phase = max(1, total_weeks // phase_count)

        for idx, topic in enumerate(topics_for_plan, start=1):
            end_week = start_week + weeks_per_phase - 1
            if idx == phase_count:
                end_week = total_weeks

            modules = self.MODULE_LIBRARY.get(topic, [topic])
            phases.append({
                "phase": idx,
                "weeks": f"{start_week}-{end_week}",
                "title": f"{topic}阶段",
                "modules": modules,
                "goal": f"掌握{topic}的核心能力，并完成对应练习"
            })
            start_week = end_week + 1

        title = f"{goal_key.replace('_', ' ').title()} 学习路径"
        description = (
            f"基于每周{available_hours}小时的可用时间制定，"
            f"覆盖{', '.join(topics_for_plan)}等核心能力。"
        )

        return {
            "title": title,
            "description": description,
            "total_weeks": total_weeks,
            "phases": phases
        }
    
    async def get_learning_path(
        self,
        path_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Optional[LearningPath]:
        """
        获取学习路径
        
        Args:
            path_id: 路径ID
            user_id: 用户ID
            db: 数据库会话
        
        Returns:
            学习路径对象
        """
        result = await db.execute(
            select(LearningPath).filter(
                LearningPath.id == path_id,
                LearningPath.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_learning_path(
        self,
        user_id: int,
        db: AsyncSession
    ) -> Optional[LearningPath]:
        """
        获取用户的活跃学习路径
        
        Args:
            user_id: 用户ID
            db: 数据库会话
        
        Returns:
            活跃的学习路径
        """
        result = await db.execute(
            select(LearningPath).filter(
                LearningPath.user_id == user_id,
                LearningPath.status == PathStatus.ACTIVE
            ).order_by(LearningPath.created_at.desc())
        )
        return result.scalars().first()
    
    async def update_learning_path(
        self,
        path_id: int,
        user_id: int,
        update_data: Dict[str, Any],
        db: AsyncSession
    ) -> Optional[LearningPath]:
        """
        更新学习路径
        
        Args:
            path_id: 路径ID
            user_id: 用户ID
            update_data: 更新数据
            db: 数据库会话
        
        Returns:
            更新后的学习路径
        """
        learning_path = await self.get_learning_path(path_id, user_id, db)
        if not learning_path:
            return None

        phases_updated = False
        for key, value in update_data.items():
            if value is not None and hasattr(learning_path, key):
                if key == "phases":
                    phases_updated = True
                setattr(learning_path, key, value)

        await db.commit()
        await db.refresh(learning_path)

        # 如果 phases 更新了，重新同步模块
        if phases_updated:
            from app.services.progress_sync_service import progress_sync_service
            await progress_sync_service.sync_path_modules(learning_path, db)
            app_logger.info(f"重新同步学习路径模块: path_id={path_id}")

        app_logger.info(f"更新学习路径: path_id={path_id}")
        return learning_path


# 全局服务实例
learning_path_service = LearningPathService()
