"""
测试对话功能脚本
"""
import asyncio
import sys
from pathlib import Path

import pytest

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.ai.rag.generator import rag_generator
from app.utils.logger import app_logger


@pytest.mark.asyncio
async def test_chat():
    """测试对话功能"""
    try:
        app_logger.info("=" * 50)
        app_logger.info("测试对话功能")
        app_logger.info("=" * 50)
        
        # 测试问题
        questions = [
            "什么是RAG？",
            "Prompt工程有哪些技巧？",
            "如何选择向量数据库？",
        ]
        
        for question in questions:
            app_logger.info(f"\n问题: {question}")
            app_logger.info("-" * 50)
            
            # 生成答案
            result = await rag_generator.generate(
                query=question,
                top_k=3,
                temperature=0.7
            )
            
            app_logger.info(f"答案: {result['answer'][:200]}...")
            app_logger.info(f"置信度: {result['confidence']:.2f}")
            app_logger.info(f"来源: {[s['text'] for s in result['sources']]}")
            app_logger.info("-" * 50)
        
        app_logger.info("\n✅ 测试完成！")
        
    except Exception as e:
        app_logger.error(f"❌ 测试失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_chat())
