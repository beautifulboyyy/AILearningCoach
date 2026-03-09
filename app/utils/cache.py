"""
缓存工具模块
"""
import json
from typing import Optional, Any
from redis import asyncio as aioredis
from app.core.config import settings
from app.utils.logger import app_logger

# Redis客户端
redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """获取Redis客户端"""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return redis_client


async def close_redis():
    """关闭Redis连接"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def cache_set(key: str, value: Any, expire: int = 3600) -> bool:
    """
    设置缓存
    
    Args:
        key: 缓存键
        value: 缓存值
        expire: 过期时间（秒），默认1小时
    
    Returns:
        是否设置成功
    """
    try:
        redis = await get_redis()
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await redis.setex(key, expire, value)
        return True
    except Exception as e:
        app_logger.error(f"缓存设置失败: {e}")
        return False


async def cache_get(key: str) -> Optional[Any]:
    """
    获取缓存
    
    Args:
        key: 缓存键
    
    Returns:
        缓存值，不存在返回None
    """
    try:
        redis = await get_redis()
        value = await redis.get(key)
        if value is None:
            return None
        
        # 尝试解析JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    except Exception as e:
        app_logger.error(f"缓存获取失败: {e}")
        return None


async def cache_delete(key: str) -> bool:
    """
    删除缓存
    
    Args:
        key: 缓存键
    
    Returns:
        是否删除成功
    """
    try:
        redis = await get_redis()
        await redis.delete(key)
        return True
    except Exception as e:
        app_logger.error(f"缓存删除失败: {e}")
        return False


async def cache_exists(key: str) -> bool:
    """
    检查缓存是否存在
    
    Args:
        key: 缓存键
    
    Returns:
        是否存在
    """
    try:
        redis = await get_redis()
        return await redis.exists(key) > 0
    except Exception as e:
        app_logger.error(f"缓存检查失败: {e}")
        return False


async def cache_set_hash(name: str, key: str, value: Any) -> bool:
    """
    设置Hash缓存
    
    Args:
        name: Hash名称
        key: Hash键
        value: Hash值
    
    Returns:
        是否设置成功
    """
    try:
        redis = await get_redis()
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await redis.hset(name, key, value)
        return True
    except Exception as e:
        app_logger.error(f"Hash缓存设置失败: {e}")
        return False


async def cache_get_hash(name: str, key: str) -> Optional[Any]:
    """
    获取Hash缓存
    
    Args:
        name: Hash名称
        key: Hash键
    
    Returns:
        Hash值，不存在返回None
    """
    try:
        redis = await get_redis()
        value = await redis.hget(name, key)
        if value is None:
            return None
        
        # 尝试解析JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    except Exception as e:
        app_logger.error(f"Hash缓存获取失败: {e}")
        return None


async def cache_get_all_hash(name: str) -> Optional[dict]:
    """
    获取所有Hash缓存
    
    Args:
        name: Hash名称
    
    Returns:
        所有Hash值字典
    """
    try:
        redis = await get_redis()
        return await redis.hgetall(name)
    except Exception as e:
        app_logger.error(f"获取所有Hash缓存失败: {e}")
        return None
