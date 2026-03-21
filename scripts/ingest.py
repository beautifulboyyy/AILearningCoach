"""
通用知识库离线导入脚本
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.ai.rag.ingest.pipeline import IngestPipeline
from app.utils.logger import app_logger


async def ingest_documents(data_dir: str = "../data"):
    pipeline = IngestPipeline()
    app_logger.info("=" * 50)
    app_logger.info("开始执行离线知识导入")
    app_logger.info("=" * 50)
    await pipeline.ingest_directory(data_dir)
    app_logger.info("=" * 50)
    app_logger.info("离线知识导入完成")
    app_logger.info("=" * 50)


async def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "../data"
    await ingest_documents(data_dir)


if __name__ == "__main__":
    asyncio.run(main())
