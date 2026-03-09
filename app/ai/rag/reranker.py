"""
Reranking重排序模块
"""
from typing import List, Dict, Any
from app.utils.logger import app_logger


class Reranker:
    """重排序器"""
    
    def __init__(self):
        """
        初始化Reranker
        
        注意：这里使用基于规则的简化版本
        完整版本可以使用BGE-reranker或其他reranking模型
        """
        pass
    
    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        对检索结果重排序
        
        Args:
            query: 查询问题
            results: 初始检索结果
            top_k: 最终返回数量
        
        Returns:
            重排序后的结果
        """
        if not results:
            return []
        
        # 简化版本：基于规则的重排序
        # 1. 关键词匹配加分
        # 2. 元数据相关性加分
        # 3. 距离分数归一化
        
        query_lower = query.lower()
        query_keywords = set(query_lower.split())
        
        scored_results = []
        for result in results:
            score = result.get("distance", 0.0)
            content = result.get("content", "").lower()
            metadata = result.get("metadata", {})
            
            # 关键词匹配加分
            content_keywords = set(content.split())
            keyword_overlap = len(query_keywords & content_keywords)
            keyword_boost = keyword_overlap * 0.1  # 每个匹配关键词加0.1分
            
            # 标题匹配加分
            title = metadata.get("title", "").lower()
            if title and any(keyword in title for keyword in query_keywords):
                keyword_boost += 0.2
            
            # 综合分数
            final_score = score + keyword_boost
            
            scored_results.append({
                **result,
                "rerank_score": final_score,
                "keyword_boost": keyword_boost
            })
        
        # 按重排序分数排序
        scored_results.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        # 返回Top-K
        final_results = scored_results[:top_k]
        
        app_logger.info(f"Reranking完成，从 {len(results)} 个结果中选出 {len(final_results)} 个")
        
        return final_results


# 全局Reranker实例
reranker = Reranker()
