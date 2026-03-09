"""
初始化数据库脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
from app.models import Base
from app.utils.logger import app_logger


async def init_database():
    """初始化数据库"""
    try:
        app_logger.info("开始初始化数据库...")
        
        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        app_logger.info("✅ 数据库初始化完成！")
        app_logger.info("所有表已创建")
        
    except Exception as e:
        app_logger.error(f"❌ 数据库初始化失败: {e}")
        raise


async def check_connection():
    """检查数据库连接"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        app_logger.info("✅ 数据库连接正常")
        return True
    except Exception as e:
        app_logger.error(f"❌ 数据库连接失败: {e}")
        return False


async def main():
    """主函数"""
    app_logger.info("=" * 50)
    app_logger.info("AI学习教练系统 - 数据库初始化")
    app_logger.info("=" * 50)
    
    # 检查连接
    if not await check_connection():
        app_logger.error("请检查数据库配置和连接")
        return
    
    # 初始化数据库
    await init_database()
    
    app_logger.info("=" * 50)
    app_logger.info("初始化完成！")
    app_logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
