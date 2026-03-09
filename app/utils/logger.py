"""
日志工具模块
"""
import sys
from loguru import logger
from app.core.config import settings


def setup_logger():
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    
    # 文件输出
    logger.add(
        settings.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=settings.LOG_LEVEL,
        rotation="100 MB",  # 文件大小超过100MB时轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        enqueue=True,  # 异步写入
    )
    
    return logger


# 创建全局logger实例
app_logger = setup_logger()
