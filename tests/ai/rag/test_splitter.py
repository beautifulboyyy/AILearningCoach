import os

os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "learning_coach")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("MILVUS_HOST", "localhost")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("DASHSCOPE_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")

from app.ai.rag.ingest.models import IngestedDocument
from app.ai.rag.ingest.splitter import DocumentSplitter


def test_document_splitter_splits_document_and_preserves_metadata():
    splitter = DocumentSplitter(chunk_size=20, chunk_overlap=0)
    document = IngestedDocument(
        source_path="data/sample.md",
        file_name="sample.md",
        file_type="md",
        content="第一段内容很长。第二段内容也很长。第三段内容继续增长。第四段内容继续增长。",
        loader_name="langchain",
        metadata={"title": "示例文档"},
    )

    chunks = splitter.split_documents([document])

    assert len(chunks) >= 2
    assert chunks[0].source_path == "data/sample.md"
    assert chunks[0].file_type == "md"
    assert chunks[0].metadata["title"] == "示例文档"
    assert chunks[0].chunk_index == 0


def test_document_splitter_preserves_related_asset_keys():
    splitter = DocumentSplitter(chunk_size=100, chunk_overlap=0)
    document = IngestedDocument(
        source_path="data/pdf/sample.pdf",
        file_name="sample.pdf",
        file_type="pdf",
        content="图 1 附近的正文内容。",
        loader_name="mineru",
        metadata={"page_idx": 3, "related_asset_keys": ["asset-1", "asset-2"]},
    )

    chunks = splitter.split_documents([document])

    assert len(chunks) == 1
    assert chunks[0].related_asset_keys == ["asset-1", "asset-2"]
