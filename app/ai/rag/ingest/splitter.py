"""
统一文档切分器
"""
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.ai.rag.ingest.models import IngestedChunk, IngestedDocument


class DocumentSplitter:
    """将统一文档对象切分为 chunk"""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def split_documents(self, documents: list[IngestedDocument]) -> list[IngestedChunk]:
        chunks: list[IngestedChunk] = []

        for document in documents:
            split_texts = self._splitter.split_text(document.content)
            related_asset_keys = document.metadata.get("related_asset_keys", [])

            for index, chunk_text in enumerate(split_texts):
                chunks.append(
                    IngestedChunk(
                        chunk_id=str(uuid4()),
                        source_path=document.source_path,
                        file_type=document.file_type,
                        chunk_index=index,
                        content=chunk_text,
                        page_start=document.page_start,
                        page_end=document.page_end,
                        metadata=dict(document.metadata),
                        related_asset_keys=list(related_asset_keys),
                    )
                )

        return chunks
