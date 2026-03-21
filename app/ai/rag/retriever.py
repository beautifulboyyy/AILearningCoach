"""
RAG 检索器模块
"""
from typing import List, Dict, Any, Optional, Callable, Awaitable

from sqlalchemy import select

from app.ai.rag.milvus_client import milvus_client
from app.ai.rag.embeddings import embedding_model
from app.db.session import async_session_maker
from app.models.knowledge import (
    KnowledgeAsset,
    KnowledgeChunk,
    KnowledgeChunkAsset,
    KnowledgeDocument,
)
from app.utils.logger import app_logger


CitationFetcher = Callable[[list[str]], Awaitable[dict[str, dict[str, Any]]]]


class RAGRetriever:
    """RAG 检索器"""

    def __init__(self, milvus=None, embedding=None, citation_fetcher: CitationFetcher | None = None):
        self.milvus = milvus or milvus_client
        self.embedding = embedding or embedding_model
        self.citation_fetcher = citation_fetcher or self._fetch_chunk_details

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        query_embedding = await self.embedding.embed_query(query)

        filter_expr = self._build_filter_expr(filters)
        search_results = self.milvus.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,
            filter_expr=filter_expr,
        )

        filtered_results = [
            result for result in search_results if result["distance"] >= similarity_threshold
        ][:top_k]

        if not filtered_results:
            return []

        chunk_ids = [result["chunk_id"] for result in filtered_results if result.get("chunk_id")]
        hydrated = await self.citation_fetcher(chunk_ids)

        enriched_results = []
        for result in filtered_results:
            chunk_id = result.get("chunk_id")
            detail = hydrated.get(chunk_id, {})
            source = {
                "document_name": detail.get("document_name", "未知文档"),
                "file_type": detail.get("file_type", result.get("file_type", "unknown")),
                "page": detail.get("page"),
                "source_path": detail.get("source_path", ""),
                "assets": detail.get("assets", []),
            }
            enriched_results.append(
                {
                    **result,
                    "content": detail.get("content", result.get("content") or result.get("preview_text", "")),
                    "source": source,
                }
            )

        app_logger.info(f"检索到 {len(enriched_results)} 个相关结果")
        return enriched_results

    def format_context(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return "未找到相关知识内容。"

        context_parts = []
        for index, result in enumerate(results, 1):
            source = result.get("source", {})
            document_name = source.get("document_name", "未知文档")
            page = source.get("page")
            page_suffix = f", 第 {page} 页" if page is not None else ""

            context_parts.append(
                f"### 知识片段 {index} (来源: {document_name}{page_suffix})\n{result['content']}\n"
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
        try:
            vector_results = await self.retrieve(query, top_k=top_k * 3)
            if not vector_results:
                return []

            from app.ai.rag.bm25 import BM25

            documents = [result["content"] for result in vector_results]
            bm25 = BM25()
            bm25.build_index(documents)
            bm25_scores = bm25.get_scores(query)

            vector_distances = [result["distance"] for result in vector_results]
            max_distance = max(vector_distances) if vector_distances else 1.0
            norm_vector_scores = [distance / max_distance for distance in vector_distances]

            max_bm25 = max(bm25_scores) if bm25_scores else 1.0
            norm_bm25_scores = [score / max_bm25 if max_bm25 > 0 else 0 for score in bm25_scores]

            for index, result in enumerate(vector_results):
                result["hybrid_score"] = (
                    vector_weight * norm_vector_scores[index] +
                    keyword_weight * norm_bm25_scores[index]
                )
                result["bm25_score"] = bm25_scores[index]

            vector_results.sort(key=lambda item: item["hybrid_score"], reverse=True)

            if use_rerank:
                from app.ai.rag.reranker import reranker

                return reranker.rerank(query, vector_results[:top_k * 2], top_k)
            return vector_results[:top_k]
        except Exception as exc:
            app_logger.warning(f"混合检索失败，降级为纯向量检索: {exc}")
            return await self.retrieve(query, top_k=top_k)

    async def _fetch_chunk_details(self, chunk_ids: list[str]) -> dict[str, dict[str, Any]]:
        if not chunk_ids:
            return {}

        async with async_session_maker() as session:
            chunk_result = await session.execute(
                select(KnowledgeChunk).where(KnowledgeChunk.id.in_(chunk_ids))
            )
            chunks = chunk_result.scalars().all()
            if not chunks:
                return {}

            document_ids = {chunk.document_id for chunk in chunks}
            documents_result = await session.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id.in_(document_ids))
            )
            documents = {document.id: document for document in documents_result.scalars().all()}

            links_result = await session.execute(
                select(KnowledgeChunkAsset).where(KnowledgeChunkAsset.chunk_id.in_(chunk_ids))
            )
            links = links_result.scalars().all()
            asset_ids = {link.asset_id for link in links}

            assets = {}
            if asset_ids:
                assets_result = await session.execute(
                    select(KnowledgeAsset).where(KnowledgeAsset.id.in_(asset_ids))
                )
                assets = {asset.id: asset for asset in assets_result.scalars().all()}

        links_by_chunk: dict[str, list[KnowledgeChunkAsset]] = {}
        for link in links:
            links_by_chunk.setdefault(link.chunk_id, []).append(link)

        hydrated: dict[str, dict[str, Any]] = {}
        for chunk in chunks:
            document = documents.get(chunk.document_id)
            chunk_assets = [
                {
                    "asset_type": assets[link.asset_id].asset_type,
                    "asset_path": assets[link.asset_id].asset_path,
                    "caption": assets[link.asset_id].caption,
                }
                for link in sorted(links_by_chunk.get(chunk.id, []), key=lambda item: item.sort_order)
                if link.asset_id in assets
            ]
            hydrated[chunk.id] = {
                "content": chunk.content,
                "document_name": document.file_name if document else "未知文档",
                "file_type": document.file_type if document else "unknown",
                "page": chunk.page_start,
                "source_path": document.source_path if document else "",
                "assets": chunk_assets,
            }

        return hydrated

    @staticmethod
    def _build_filter_expr(filters: Optional[Dict[str, Any]]) -> Optional[str]:
        if not filters:
            return None

        conditions = []
        if "file_type" in filters:
            conditions.append(f"file_type == '{filters['file_type']}'")
        if "document_id" in filters:
            conditions.append(f"document_id == '{filters['document_id']}'")
        return " and ".join(conditions) if conditions else None


rag_retriever = RAGRetriever()
