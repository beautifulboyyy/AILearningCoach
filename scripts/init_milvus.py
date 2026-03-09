"""
初始化Milvus向量数据库脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.ai.rag.milvus_client import milvus_client
from app.utils.logger import app_logger


def main():
    """主函数"""
    try:
        app_logger.info("=" * 50)
        app_logger.info("AI学习教练系统 - Milvus初始化")
        app_logger.info("=" * 50)
        
        # 连接到Milvus
        app_logger.info("正在连接到Milvus...")
        milvus_client.connect()
        app_logger.info("✅ 已连接到Milvus")
        
        # 创建集合
        app_logger.info("正在创建知识库集合...")
        milvus_client.create_collection(drop_if_exists=False)
        app_logger.info("✅ 知识库集合已创建")
        
        # 获取集合信息
        stats = milvus_client.get_stats()
        app_logger.info(f"集合名称: {stats['name']}")
        app_logger.info(f"实体数量: {stats['num_entities']}")
        
        app_logger.info("=" * 50)
        app_logger.info("Milvus初始化完成！")
        app_logger.info("=" * 50)
        
    except Exception as e:
        app_logger.error(f"❌ Milvus初始化失败: {e}")
        raise
    finally:
        milvus_client.disconnect()


if __name__ == "__main__":
    main()
