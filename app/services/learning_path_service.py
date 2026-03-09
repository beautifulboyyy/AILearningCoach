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
            
            # 构建规划请求Prompt
            profile_info = ""
            if profile:
                profile_info = f"""
## 用户背景
- 职业：{profile.occupation or '未知'}
- 技术背景：{json.dumps(profile.technical_background or {}, ensure_ascii=False)}
- 当前水平：{json.dumps(profile.current_level or {}, ensure_ascii=False)}
"""
            
            prior_info = ""
            if prior_knowledge:
                prior_info = f"\n已有知识：{json.dumps(prior_knowledge, ensure_ascii=False)}"
            
            # 简化Prompt以减少生成时间（P0优化：从2000 tokens减少到800 tokens）
            planning_prompt = f"""生成学习路径（JSON格式，简洁回答）：

目标：{learning_goal}
每周时间：{available_hours}小时
{prior_info}

模块：1.Prompt工程 2.Function Calling 3.RAG系统 4.Agent开发 5.MCP

返回JSON（不超过500字）：
{{
    "title": "路径标题",
    "description": "简短描述",
    "total_weeks": 8,
    "phases": [
        {{"phase": 1, "weeks": "1-2", "title": "阶段1", "modules": ["讲03-07"], "goal": "目标"}},
        {{"phase": 2, "weeks": "3-4", "title": "阶段2", "modules": ["讲08-10"], "goal": "目标"}}
    ]
}}

只返回JSON。"""
            
            # 调用LLM生成规划（减少max_tokens以加快响应）
            response = await llm.generate(
                messages=[{"role": "user", "content": planning_prompt}],
                temperature=0.5,  # 降低temperature以加快生成
                max_tokens=800  # 从2000减少到800，大幅提升速度
            )
            
            # 解析JSON
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = response.strip()
            
            learning_plan = json.loads(json_str)
            
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
