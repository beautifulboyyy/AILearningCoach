"""
文档加载器注册中心
"""
from pathlib import Path

from app.ai.rag.ingest.base import BaseDocumentLoader


class LoaderRegistry:
    """根据扩展名查找合适的文档加载器"""

    def __init__(self):
        self._loaders: dict[str, BaseDocumentLoader] = {}

    def register(self, loader: BaseDocumentLoader) -> None:
        for extension in loader.supported_extensions:
            self._loaders[extension.lower()] = loader

    def get_loader(self, path: Path) -> BaseDocumentLoader:
        extension = path.suffix.lower()
        loader = self._loaders.get(extension)
        if loader is None:
            raise ValueError(f"No loader registered for file: {path}")
        return loader
