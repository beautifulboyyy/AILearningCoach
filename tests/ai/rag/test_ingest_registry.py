import os
from pathlib import Path
from types import SimpleNamespace

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
from app.ai.rag.ingest.loaders.langchain_loader import LangChainDocumentLoader
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


def test_langchain_document_loader_supports_txt_docx_md():
    loader = LangChainDocumentLoader()

    assert loader.supported_extensions == {".txt", ".docx", ".md"}


def test_langchain_document_loader_maps_loaded_documents_to_ingested_documents(tmp_path, monkeypatch):
    source_file = tmp_path / "lesson.md"
    source_file.write_text("# 标题\n\n内容段落", encoding="utf-8")

    fake_loaded_documents = [
        SimpleNamespace(page_content="# 标题\n\n内容段落", metadata={"title": "标题"})
    ]

    class FakeLoader:
        def __init__(self, path, encoding=None):
            self.path = path
            self.encoding = encoding

        def load(self):
            return fake_loaded_documents

    monkeypatch.setattr(
        "app.ai.rag.ingest.loaders.langchain_loader.TextLoader",
        FakeLoader,
    )

    loader = LangChainDocumentLoader()
    documents = __import__("asyncio").run(loader.load(source_file))

    assert len(documents) == 1
    assert documents[0].file_name == "lesson.md"
    assert documents[0].file_type == "md"
    assert documents[0].loader_name == "langchain"
    assert documents[0].metadata["title"] == "标题"
