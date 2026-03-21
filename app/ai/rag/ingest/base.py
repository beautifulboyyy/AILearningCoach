"""
摄取 Loader 基础接口
"""
from abc import ABC, abstractmethod
from pathlib import Path


class BaseDocumentLoader(ABC):
    """文档加载器基础接口"""

    supported_extensions: set[str] = set()

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_extensions

    @abstractmethod
    async def load(self, path: Path):
        """将文件解析为统一文档对象列表"""
