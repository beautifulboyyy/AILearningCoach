"""
通用知识摄取模块
"""

from app.ai.rag.ingest.base import BaseDocumentLoader
from app.ai.rag.ingest.models import IngestedAsset, IngestedChunk, IngestedDocument
from app.ai.rag.ingest.persistence import PersistenceService
from app.ai.rag.ingest.pipeline import IngestPipeline
from app.ai.rag.ingest.registry import LoaderRegistry
from app.ai.rag.ingest.splitter import DocumentSplitter

__all__ = [
    "BaseDocumentLoader",
    "IngestedDocument",
    "IngestedChunk",
    "IngestedAsset",
    "LoaderRegistry",
    "DocumentSplitter",
    "PersistenceService",
    "IngestPipeline",
]
