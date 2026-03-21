"""
摄取加载器集合
"""

from app.ai.rag.ingest.loaders.langchain_loader import LangChainDocumentLoader
from app.ai.rag.ingest.loaders.mineru_pdf_loader import MinerUPdfLoader

__all__ = ["LangChainDocumentLoader", "MinerUPdfLoader"]
