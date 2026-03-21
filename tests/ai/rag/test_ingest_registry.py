import os
from pathlib import Path

os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "learning_coach")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("MILVUS_HOST", "localhost")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("DASHSCOPE_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")

from app.ai.rag.ingest.base import BaseDocumentLoader
from app.ai.rag.ingest.registry import LoaderRegistry


class DummyLoader(BaseDocumentLoader):
    supported_extensions = {".md"}

    async def load(self, path: Path):
        return []


def test_loader_registry_returns_registered_loader_for_extension():
    registry = LoaderRegistry()
    loader = DummyLoader()
    registry.register(loader)

    matched_loader = registry.get_loader(Path("lesson.md"))

    assert matched_loader is loader


def test_loader_registry_raises_for_unsupported_extension():
    registry = LoaderRegistry()
    registry.register(DummyLoader())

    try:
        registry.get_loader(Path("lesson.pdf"))
    except ValueError as exc:
        assert "lesson.pdf" in str(exc)
    else:
        raise AssertionError("Expected unsupported extension to raise ValueError")
