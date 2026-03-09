"""
创建测试用户脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.db.session import async_session_maker
from app.models.user import User
from app.models.profile import UserProfile
from app.core.security import get_password_hash
from app.utils.logger import app_logger


async def create_test_user():
    """创建测试用户"""
    try:
        app_logger.info("=" * 50)
        app_logger.info("创建测试用户")
        app_logger.info("=" * 50)
        
        async with async_session_maker() as db:
            # 创建测试用户
            test_user = User(
                username="testuser",
                email="test@example.com",
                password_hash=get_password_hash("test123456"),
                is_active=True,
                is_superuser=False
            )
            db.add(test_user)
            await db.flush()
            
            # 创建用户画像
            profile = UserProfile(
                user_id=test_user.id,
                name="测试用户",
                occupation="软件工程师",
                technical_background={
                    "programming_languages": ["Python", "JavaScript"],
                    "frameworks": ["FastAPI", "React"],
                    "experience_years": 3
                },
                learning_goal="systematic_learning",
                learning_preference={
                    "content_type": "practical",
                    "explanation_style": "detailed",
                    "learning_pace": "medium"
                },
                current_level={
                    "prompt_engineering": "beginner",
                    "rag": "not_started",
                    "agent": "not_started"
                }
            )
            db.add(profile)
            
            await db.commit()
            
            app_logger.info("✅ 测试用户创建成功！")
            app_logger.info(f"用户名: testuser")
            app_logger.info(f"密码: test123456")
            app_logger.info(f"邮箱: test@example.com")
        
        app_logger.info("=" * 50)
        
    except Exception as e:
        app_logger.error(f"❌ 创建测试用户失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_test_user())
