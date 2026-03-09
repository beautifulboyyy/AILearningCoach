"""
RAG检索器模块
"""
from typing import List, Dict, Any, Optional
from app.ai.rag.milvus_client import milvus_client
from app.ai.rag.embeddings import embedding_model
from app.utils.logger import app_logger


class RAGRetriever:
    """RAG检索器"""
    
    def __init__(self):
        self.milvus = milvus_client
        self.embedding = embedding_model
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相关知识
        
        Args:
            query: 查询问题
            top_k: 返回前K个结果
            similarity_threshold: 相似度阈值
            filters: 过滤条件（如难度等级、讲义编号）
        
        Returns:
            检索结果列表
        """
        # 1. 向量化查询
        query_embedding = await self.embedding.embed_query(query)
        
        # 2. 构建过滤表达式
        filter_expr = None
        if filters:
            conditions = []
            if "lecture_number" in filters:
                conditions.append(f"metadata['lecture_number'] == {filters['lecture_number']}")
            if "difficulty_level" in filters:
                conditions.append(f"metadata['difficulty_level'] == '{filters['difficulty_level']}'")
            
            if conditions:
                filter_expr = " and ".join(conditions)
        
        # 3. 向量搜索
        search_results = self.milvus.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # 多检索一些，后续过滤
            filter_expr=filter_expr
        )
        
        # 4. 过滤低相似度结果
        filtered_results = [
            result for result in search_results
            if result["distance"] >= similarity_threshold
        ][:top_k]
        
        app_logger.info(f"检索到 {len(filtered_results)} 个相关结果")
        
        return filtered_results
    
    def format_context(self, results: List[Dict[str, Any]]) -> str:
        """
        格式化检索结果为上下文
        
        Args:
            results: 检索结果
        
        Returns:
            格式化的上下文文本
        """
        if not results:
            return "未找到相关知识内容。"
        
        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            lecture = metadata.get("lecture_number", "未知")
            section = metadata.get("section", "")
            title = metadata.get("title", "")
            
            # 构建来源信息
            source = f"讲{lecture}"
            if section:
                source += f"-第{section}节"
            if title:
                source += f": {title}"
            
            # 构建上下文片段
            context_parts.append(
                f"### 知识片段 {i} (来源: {source})\n{result['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    async def hybrid_retrieve(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        use_rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        混合检索（向量检索 + 关键词检索 + Reranking）
        
        Args:
            query: 查询问题
            top_k: 返回前K个结果
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
            use_rerank: 是否使用Reranking
        
        Returns:
            混合检索结果
        """
        try:
            # 1. 向量检索（获取更多候选，用于混合）
            vector_results = await self.retrieve(query, top_k=top_k * 3)
            
            if not vector_results:
                return []
            
            # 2. BM25关键词检索（基于向量检索结果）
            from app.ai.rag.bm25 import BM25
            
            # 准备文档
            documents = [r["content"] for r in vector_results]
            
            # 构建BM25索引
            bm25 = BM25()
            bm25.build_index(documents)
            
            # BM25检索
            bm25_scores = bm25.get_scores(query)
            
            # 3. 混合分数计算
            # 归一化向量分数（距离）
            vector_distances = [r["distance"] for r in vector_results]
            max_distance = max(vector_distances) if vector_distances else 1.0
            norm_vector_scores = [d / max_distance for d in vector_distances]
            
            # 归一化BM25分数
            max_bm25 = max(bm25_scores) if bm25_scores else 1.0
            norm_bm25_scores = [s / max_bm25 if max_bm25 > 0 else 0 for s in bm25_scores]
            
            # 计算混合分数
            for i, result in enumerate(vector_results):
                hybrid_score = (
                    vector_weight * norm_vector_scores[i] +
                    keyword_weight * norm_bm25_scores[i]
                )
                result["hybrid_score"] = hybrid_score
                result["bm25_score"] = bm25_scores[i]
            
            # 按混合分数排序
            vector_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
            
            # 4. Reranking（可选）
            if use_rerank:
                from app.ai.rag.reranker import reranker
                final_results = reranker.rerank(query, vector_results[:top_k * 2], top_k)
            else:
                final_results = vector_results[:top_k]
            
            app_logger.info(
                f"混合检索完成: 向量权重={vector_weight}, "
                f"关键词权重={keyword_weight}, "
                f"Rerank={'启用' if use_rerank else '禁用'}"
            )
            
            return final_results
            
        except Exception as e:
            app_logger.warning(f"混合检索失败，降级为纯向量检索: {e}")
            # 降级为纯向量检索
            return await self.retrieve(query, top_k=top_k)


# 全局检索器实例
rag_retriever = RAGRetriever()
