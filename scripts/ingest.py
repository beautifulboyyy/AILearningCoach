"""
知识库导入脚本
将课程讲义导入到Milvus向量数据库
"""
import asyncio
import sys
import re
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from app.ai.rag.milvus_client import milvus_client
from app.ai.rag.embeddings import embedding_model
from app.models.knowledge import KnowledgeChunk
from app.db.session import async_session_maker
from app.utils.logger import app_logger


class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> List[str]:
        """
        分割文本为chunks
        
        Args:
            text: 输入文本
        
        Returns:
            文本块列表
        """
        # 按段落分割
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果当前chunk + 新段落不超过大小限制
            if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                # 保存当前chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 开始新chunk
                if len(paragraph) > self.chunk_size:
                    # 段落太长，需要进一步分割
                    sentences = re.split(r'[。！？\n]', paragraph)
                    temp_chunk = ""
                    for sentence in sentences:
                        if len(temp_chunk) + len(sentence) <= self.chunk_size:
                            temp_chunk += sentence + "。"
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = sentence + "。"
                    if temp_chunk:
                        current_chunk = temp_chunk
                else:
                    current_chunk = paragraph + "\n\n"
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_metadata(self, filepath: Path) -> Dict[str, Any]:
        """
        从文件名和内容中提取元数据
        
        Args:
            filepath: 文件路径
        
        Returns:
            元数据字典
        """
        filename = filepath.stem
        
        # 尝试从文件名中提取讲义编号
        # 例如: "讲14-RAG系统.md" -> lecture_number=14
        match = re.match(r'讲(\d+)', filename)
        lecture_number = int(match.group(1)) if match else 0
        
        return {
            "lecture_number": lecture_number,
            "filename": filename,
            "source": str(filepath)
        }


async def ingest_documents(data_dir: str = "data/lectures"):
    """
    导入文档到向量数据库
    
    Args:
        data_dir: 文档目录路径
    """
    try:
        app_logger.info("=" * 50)
        app_logger.info("开始导入知识库")
        app_logger.info("=" * 50)
        
        # 检查数据目录
        data_path = Path(data_dir)
        if not data_path.exists():
            app_logger.error(f"数据目录不存在: {data_dir}")
            app_logger.info("请创建目录并放入课程讲义文件（Markdown格式）")
            return
        
        # 获取所有Markdown文件
        md_files = list(data_path.glob("*.md"))
        if not md_files:
            app_logger.warning(f"在 {data_dir} 中没有找到Markdown文件")
            return
        
        app_logger.info(f"找到 {len(md_files)} 个文档文件")
        
        # 连接Milvus
        milvus_client.connect()
        
        # 确保集合存在
        milvus_client.create_collection(drop_if_exists=False)
        
        # 文档处理器
        processor = DocumentProcessor()
        
        # 连接数据库
        async with async_session_maker() as db:
            total_chunks = 0
            
            # 处理每个文件
            for filepath in md_files:
                app_logger.info(f"处理文件: {filepath.name}")
                
                # 读取文件内容
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取元数据
                metadata = processor.extract_metadata(filepath)
                
                # 分割文本
                chunks = processor.split_text(content)
                app_logger.info(f"  分割为 {len(chunks)} 个文本块")
                
                # 向量化chunks
                app_logger.info(f"  正在向量化...")
                embeddings = await embedding_model.embed_texts(chunks)
                
                # 准备数据
                milvus_data = []
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    vector_id = f"{metadata['lecture_number']}_{i}"
                    
                    # 保存到PostgreSQL
                    db_chunk = KnowledgeChunk(
                        lecture_number=metadata['lecture_number'],
                        section=None,
                        content=chunk,
                        vector_id=vector_id,
                        meta_info=metadata
                    )
                    db.add(db_chunk)
                    
                    # 准备Milvus数据
                    milvus_data.append({
                        "vector_id": vector_id,
                        "content": chunk[:8000],  # Milvus字段限制
                        "embedding": embedding,
                        "metadata": metadata
                    })
                
                # 插入到Milvus
                if milvus_data:
                    milvus_client.insert(milvus_data)
                    app_logger.info(f"  ✅ 已导入 {len(milvus_data)} 个文本块")
                    total_chunks += len(milvus_data)
            
            # 提交数据库
            await db.commit()
            
            app_logger.info("=" * 50)
            app_logger.info(f"知识库导入完成！")
            app_logger.info(f"总计导入: {total_chunks} 个文本块")
            app_logger.info("=" * 50)
            
    except Exception as e:
        app_logger.error(f"❌ 知识库导入失败: {e}")
        raise
    finally:
        milvus_client.disconnect()


async def main():
    """主函数"""
    import sys
    
    # 获取数据目录参数
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data/lectures"
    
    await ingest_documents(data_dir)


if __name__ == "__main__":
    asyncio.run(main())
