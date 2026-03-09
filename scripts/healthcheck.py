"""
健康检查脚本 - Docker健康检查使用
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import engine
from app.utils.cache import get_redis
import json


async def check_database():
    """检查数据库连接"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "PostgreSQL连接正常"
    except Exception as e:
        return False, f"PostgreSQL连接失败: {str(e)[:100]}"


async def check_redis():
    """检查Redis连接"""
    try:
        redis = await get_redis()
        await redis.ping()
        return True, "Redis连接正常"
    except Exception as e:
        return False, f"Redis连接失败: {str(e)[:100]}"


async def check_milvus():
    """检查Milvus连接"""
    try:
        from app.ai.rag.milvus_client import milvus_client
        milvus_client.connect()
        stats = milvus_client.get_stats()
        milvus_client.disconnect()
        return True, f"Milvus连接正常，集合: {stats['name']}"
    except Exception as e:
        return False, f"Milvus连接失败: {str(e)[:100]}"


async def main():
    """主健康检查函数"""
    results = {
        "status": "healthy",
        "checks": {}
    }
    
    # 检查数据库
    db_ok, db_msg = await check_database()
    results["checks"]["database"] = {"status": "ok" if db_ok else "error", "message": db_msg}
    
    # 检查Redis
    redis_ok, redis_msg = await check_redis()
    results["checks"]["redis"] = {"status": "ok" if redis_ok else "error", "message": redis_msg}
    
    # 检查Milvus（可选）
    milvus_ok, milvus_msg = await check_milvus()
    results["checks"]["milvus"] = {"status": "ok" if milvus_ok else "warning", "message": milvus_msg}
    
    # 判断总体状态
    if not db_ok or not redis_ok:
        results["status"] = "unhealthy"
        print(json.dumps(results, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    if not milvus_ok:
        results["status"] = "degraded"
    
    print(json.dumps(results, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False))
        sys.exit(1)
