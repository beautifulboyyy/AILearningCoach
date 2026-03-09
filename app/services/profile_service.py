"""
用户画像服务
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.profile import UserProfile
from app.models.user import User
from app.ai.rag.llm import llm
from app.utils.logger import app_logger
import json


class ProfileService:
    """用户画像服务"""
    
    async def get_profile(self, user_id: int, db: AsyncSession) -> Optional[UserProfile]:
        """
        获取用户画像
        
        Args:
            user_id: 用户ID
            db: 数据库会话
        
        Returns:
            用户画像对象
        """
        result = await db.execute(
            select(UserProfile).filter(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_profile(
        self,
        user_id: int,
        profile_data: Dict[str, Any],
        db: AsyncSession
    ) -> UserProfile:
        """
        创建用户画像
        
        Args:
            user_id: 用户ID
            profile_data: 画像数据
            db: 数据库会话
        
        Returns:
            创建的用户画像
        """
        profile = UserProfile(user_id=user_id, **profile_data)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
        app_logger.info(f"创建用户画像: user_id={user_id}")
        return profile
    
    async def update_profile(
        self,
        user_id: int,
        profile_data: Dict[str, Any],
        db: AsyncSession
    ) -> Optional[UserProfile]:
        """
        更新用户画像
        
        Args:
            user_id: 用户ID
            profile_data: 画像数据
            db: 数据库会话
        
        Returns:
            更新后的用户画像
        """
        profile = await self.get_profile(user_id, db)
        if not profile:
            return None
        
        # 更新字段
        for key, value in profile_data.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)
        
        await db.commit()
        await db.refresh(profile)
        
        app_logger.info(f"更新用户画像: user_id={user_id}")
        return profile
    
    async def generate_profile_from_conversation(
        self,
        conversation_text: str,
        user_id: int,
        db: AsyncSession
    ) -> UserProfile:
        """
        从对话中自动生成用户画像
        
        Args:
            conversation_text: 对话文本
            user_id: 用户ID
            db: 数据库会话
        
        Returns:
            生成的用户画像
        """
        # 使用LLM提取用户信息
        extraction_prompt = f"""请从以下对话中提取用户的背景信息，并以JSON格式返回。

对话内容：
{conversation_text}

请提取以下信息（如果对话中没有提到，设为null）：
1. name: 姓名
2. age: 年龄
3. occupation: 职业
4. technical_background: 技术背景（包含编程语言、框架、经验年限）
5. learning_goal: 学习目标（job_hunting/project/systematic_learning）
6. learning_preference: 学习偏好（内容类型、讲解风格、学习节奏）
7. current_level: 当前各模块水平（prompt_engineering/rag/agent等）

请只返回JSON格式，不要有其他文字。
"""
        
        try:
            response = await llm.generate(
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            # 解析JSON
            # 尝试提取JSON（可能被markdown包裹）
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
            
            extracted_info = json.loads(json_str)
            
            # 获取或创建画像
            profile = await self.get_profile(user_id, db)
            if profile:
                # 更新现有画像
                profile = await self.update_profile(user_id, extracted_info, db)
            else:
                # 创建新画像
                profile = await self.create_profile(user_id, extracted_info, db)
            
            app_logger.info(f"从对话中生成用户画像: user_id={user_id}")
            return profile
            
        except Exception as e:
            app_logger.error(f"生成画像失败: {e}")
            raise
    
    def format_profile_for_prompt(self, profile: UserProfile) -> str:
        """
        格式化用户画像为Prompt文本
        
        Args:
            profile: 用户画像对象
        
        Returns:
            格式化的文本
        """
        parts = []
        
        if profile.name:
            parts.append(f"姓名：{profile.name}")
        
        if profile.occupation:
            parts.append(f"职业：{profile.occupation}")
        
        if profile.technical_background:
            bg = profile.technical_background
            if bg.get("programming_languages"):
                parts.append(f"编程语言：{', '.join(bg['programming_languages'])}")
            if bg.get("experience_years"):
                parts.append(f"工作经验：{bg['experience_years']}年")
        
        if profile.learning_goal:
            goal_map = {
                "job_hunting": "求职准备",
                "project": "项目实战",
                "systematic_learning": "系统学习"
            }
            parts.append(f"学习目标：{goal_map.get(profile.learning_goal, profile.learning_goal)}")
        
        if profile.current_level:
            levels = []
            for module, level in profile.current_level.items():
                levels.append(f"{module}: {level}")
            if levels:
                parts.append(f"当前水平：{', '.join(levels)}")
        
        return "\n".join(parts) if parts else "暂无画像信息"


# 全局服务实例
profile_service = ProfileService()


# 添加缺少的import
import re
