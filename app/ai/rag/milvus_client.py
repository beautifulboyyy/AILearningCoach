"""
Milvus向量数据库客户端
"""
from typing import List, Optional, Dict, Any
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)
from app.core.config import settings
from app.utils.logger import app_logger


class MilvusClient:
    """Milvus客户端封装"""
    
    def __init__(self):
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.collection: Optional[Collection] = None
        self._connected = False
    
    def connect(self):
        """连接到Milvus"""
        if not self._connected:
            try:
                connections.connect(
                    alias="default",
                    host=settings.MILVUS_HOST,
                    port=settings.MILVUS_PORT,
                )
                self._connected = True
                app_logger.info(f"已连接到Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
            except Exception as e:
                app_logger.error(f"连接Milvus失败: {e}")
                raise
    
    def disconnect(self):
        """断开Milvus连接"""
        if self._connected:
            connections.disconnect(alias="default")
            self._connected = False
            app_logger.info("已断开Milvus连接")
    
    def create_collection(self, drop_if_exists: bool = False):
        """
        创建集合
        
        Args:
            drop_if_exists: 如果集合已存在是否删除
        """
        self.connect()
        self.collection = None
        
        # 检查集合是否存在
        if utility.has_collection(self.collection_name):
            if drop_if_exists:
                utility.drop_collection(self.collection_name)
                app_logger.info(f"已删除现有集合: {self.collection_name}")
            else:
                app_logger.info(f"集合已存在: {self.collection_name}")
                self.collection = Collection(self.collection_name)
                return
        
        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="preview_text", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="file_type", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="page_idx", dtype=DataType.INT64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]
        
        # 创建schema
        schema = CollectionSchema(
            fields=fields,
            description="AI学习教练知识库"
        )
        
        # 创建集合
        self.collection = Collection(
            name=self.collection_name,
            schema=schema,
        )
        
        # 创建索引
        index_params = {
            "metric_type": "IP",  # 内积（适合归一化后的向量）
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        app_logger.info(f"已创建集合: {self.collection_name}")

    def ensure_collection(self):
        """确保集合存在，适合在离线导入前做幂等初始化。"""
        self.connect()
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            return self.collection

        self.create_collection(drop_if_exists=False)
        return self.collection
    
    def get_collection(self) -> Collection:
        """获取集合"""
        self.connect()
        if self.collection is None:
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
            else:
                self.create_collection(drop_if_exists=False)
        elif not utility.has_collection(self.collection_name):
            self.collection = None
            self.create_collection(drop_if_exists=False)
        return self.collection
    
    def insert(self, data: List[Dict[str, Any]]):
        """
        插入数据
        
        Args:
            data: 数据列表，每个元素包含 vector_id, chunk_id, document_id, preview_text, file_type, page_idx, embedding, metadata
        """
        collection = self.ensure_collection()
        
        # 准备数据
        vector_ids = [item["vector_id"] for item in data]
        chunk_ids = [item["chunk_id"] for item in data]
        document_ids = [item["document_id"] for item in data]
        preview_texts = [item.get("preview_text", "") for item in data]
        file_types = [item.get("file_type", "") for item in data]
        page_indexes = [item.get("page_idx") if item.get("page_idx") is not None else -1 for item in data]
        embeddings = [item["embedding"] for item in data]
        metadata_list = [item.get("metadata", {}) for item in data]

        # 插入数据
        collection.insert([vector_ids, chunk_ids, document_ids, preview_texts, file_types, page_indexes, embeddings, metadata_list])
        collection.flush()
        
        app_logger.info(f"已插入 {len(data)} 条数据到集合: {self.collection_name}")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        向量搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回前K个结果
            filter_expr: 过滤表达式
        
        Returns:
            搜索结果列表
        """
        collection = self.get_collection()
        collection.load()
        
        # 搜索参数
        search_params = {
            "metric_type": "IP",
            "params": {"nprobe": 10}
        }
        
        # 执行搜索
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["vector_id", "chunk_id", "document_id", "preview_text", "file_type", "page_idx", "metadata"]
        )
        
        # 格式化结果
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "id": hit.id,
                    "vector_id": hit.entity.get("vector_id"),
                    "chunk_id": hit.entity.get("chunk_id"),
                    "document_id": hit.entity.get("document_id"),
                    "preview_text": hit.entity.get("preview_text"),
                    "file_type": hit.entity.get("file_type"),
                    "page_idx": hit.entity.get("page_idx"),
                    "metadata": hit.entity.get("metadata", {}),
                    "distance": hit.distance,
                })
        
        return formatted_results
    
    def delete(self, expr: str):
        """
        删除数据
        
        Args:
            expr: 删除表达式，如 'vector_id in ["id1", "id2"]'
        """
        collection = self.get_collection()
        collection.load()
        collection.delete(expr)
        collection.flush()
        app_logger.info(f"已从集合 {self.collection_name} 删除数据: {expr}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        collection = self.get_collection()
        return {
            "name": collection.name,
            "num_entities": collection.num_entities,
            "description": collection.description,
        }


# 全局Milvus客户端实例
milvus_client = MilvusClient()
