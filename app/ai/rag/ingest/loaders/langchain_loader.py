"""
基于 LangChain 的通用文档加载器
"""
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, TextLoader

from app.ai.rag.ingest.base import BaseDocumentLoader
from app.ai.rag.ingest.models import IngestedDocument


class LangChainDocumentLoader(BaseDocumentLoader):
    """使用 LangChain 处理 txt、docx、md 文档"""

    supported_extensions = {".txt", ".docx", ".md"}

    def _build_loader(self, path: Path):
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return TextLoader(str(path), encoding="utf-8")
        if suffix == ".docx":
            return Docx2txtLoader(str(path))
        raise ValueError(f"Unsupported file type: {path}")

    async def load(self, path: Path) -> list[IngestedDocument]:
        loader = self._build_loader(path)
        loaded_documents = loader.load()

        return [
            IngestedDocument(
                source_path=str(path),
                file_name=path.name,
                file_type=path.suffix.lower().lstrip("."),
                content=document.page_content,
                loader_name="langchain",
                metadata=dict(getattr(document, "metadata", {}) or {}),
            )
            for document in loaded_documents
        ]
