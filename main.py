"""
AI学习教练系统 - 主应用
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from app.core.config import settings
from app.api.v1.api import api_router
from app.utils.logger import app_logger
from app.utils.cache import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    app_logger.info("=== 应用启动 ===")
    app_logger.info(f"项目名称: {settings.PROJECT_NAME}")
    app_logger.info(f"环境: {settings.ENVIRONMENT}")
    app_logger.info(f"调试模式: {settings.DEBUG}")
    
    yield
    
    # 关闭时执行
    app_logger.info("=== 应用关闭 ===")
    await close_redis()


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="基于LLM的智能学习教练系统API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["健康检查"])
async def root():
    """根路径 - 健康检查"""
    return {
        "message": "AI学习教练系统",
        "status": "运行中",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """
    健康检查端点
    
    检查系统各组件状态：
    - 数据库连接
    - Redis连接
    - Milvus连接（可选）
    """
    from sqlalchemy import text
    from app.db.session import engine
    from app.utils.cache import get_redis
    
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # 检查数据库
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)[:50]}"
        health_status["status"] = "unhealthy"
    
    # 检查Redis
    try:
        redis = await get_redis()
        await redis.ping()
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)[:50]}"
        health_status["status"] = "degraded"
    
    # 检查Milvus（可选，失败不影响健康状态）
    try:
        from app.ai.rag.milvus_client import milvus_client
        milvus_client.connect()
        milvus_client.disconnect()
        health_status["checks"]["milvus"] = "ok"
    except Exception:
        health_status["checks"]["milvus"] = "unavailable"
    
    return health_status


@app.get("/ready", tags=["健康检查"])
async def readiness_check():
    """
    就绪检查端点
    
    检查系统是否已完成初始化并准备好处理请求
    """
    from pathlib import Path
    
    ready_status = {
        "ready": False,
        "checks": {}
    }
    
    # 检查初始化标记
    init_marker = Path("/tmp/init/.initialized")
    if init_marker.exists():
        ready_status["checks"]["initialization"] = "completed"
        ready_status["ready"] = True
    else:
        ready_status["checks"]["initialization"] = "pending"
    
    # 检查数据库表
    try:
        from sqlalchemy import text
        from app.db.session import engine
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
            )
            table_count = result.scalar()
            if table_count > 0:
                ready_status["checks"]["database_tables"] = f"ok ({table_count} tables)"
            else:
                ready_status["checks"]["database_tables"] = "no tables"
                ready_status["ready"] = False
    except Exception as e:
        ready_status["checks"]["database_tables"] = f"error: {str(e)[:50]}"
        ready_status["ready"] = False
    
    return ready_status


# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    app_logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误" if not settings.DEBUG else str(exc),
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
