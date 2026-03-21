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

from pathlib import Path
from types import SimpleNamespace

from app.models.knowledge import (
    IngestJob,
    KnowledgeAsset,
    KnowledgeChunk,
    KnowledgeChunkAsset,
    KnowledgeDocument,
)


def test_knowledge_models_expose_document_chunk_asset_relationships():
    document_columns = KnowledgeDocument.__table__.columns
    chunk_columns = KnowledgeChunk.__table__.columns
    asset_columns = KnowledgeAsset.__table__.columns
    relation_columns = KnowledgeChunkAsset.__table__.columns
    ingest_job_columns = IngestJob.__table__.columns

    assert "id" in document_columns
    assert "source_path" in document_columns
    assert "file_hash" in document_columns
    assert "status" in document_columns

    assert "id" in chunk_columns
    assert "document_id" in chunk_columns
    assert "vector_id" in chunk_columns
    assert "page_start" in chunk_columns
    assert "page_end" in chunk_columns

    assert "id" in asset_columns
    assert "document_id" in asset_columns
    assert "asset_path" in asset_columns
    assert "caption" in asset_columns

    assert "chunk_id" in relation_columns
    assert "asset_id" in relation_columns
    assert "relation_type" in relation_columns

    assert "source_path" in ingest_job_columns
    assert "file_hash" in ingest_job_columns
    assert "status" in ingest_job_columns
    assert "error_message" in ingest_job_columns


def test_knowledge_chunk_asset_relation_points_to_chunk_and_asset():
    relation_fk_targets = {
        foreign_key.target_fullname
        for foreign_key in KnowledgeChunkAsset.__table__.foreign_keys
    }

    assert "knowledge_chunks.id" in relation_fk_targets
    assert "knowledge_assets.id" in relation_fk_targets


def test_mineru_pdf_loader_extracts_assets_with_relative_paths(tmp_path):
    from app.ai.rag.ingest.loaders.mineru_pdf_loader import MinerUPdfLoader

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    image = SimpleNamespace(
        path="images/figure-1.png",
        name="figure-1.png",
        data=b"image",
    )

    def fake_parser(path: Path):
        return {
            "job_id": "job-1",
            "images": [image],
            "content_list": [
                {
                    "type": "image",
                    "page_idx": 2,
                    "img_path": "images/figure-1.png",
                    "image_caption": [{"text": "系统架构图"}],
                    "bbox": [0, 0, 10, 10],
                },
                {
                    "type": "text",
                    "page_idx": 2,
                    "text": "这里是图片附近的正文。",
                    "bbox": [0, 11, 10, 20],
                },
            ]
        }

    loader = MinerUPdfLoader(asset_root=tmp_path / "knowledge_assets", parser=fake_parser)
    documents = __import__("asyncio").run(loader.load(pdf_path))

    assert len(documents) == 1
    assert documents[0].file_type == "pdf"
    assert documents[0].metadata["related_asset_keys"] == ["image-0"]
    assert len(documents[0].assets) == 1
    assert documents[0].assets[0].asset_key == "image-0"
    assert documents[0].assets[0].asset_path == "sample/job-1/figure-1.png"
    assert documents[0].assets[0].caption == "系统架构图"


def test_mineru_pdf_loader_falls_back_to_same_page_asset_linking(tmp_path):
    from app.ai.rag.ingest.loaders.mineru_pdf_loader import MinerUPdfLoader

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    image = SimpleNamespace(
        path="images/figure-2.png",
        name="figure-2.png",
        data=b"image",
    )

    def fake_parser(path: Path):
        return {
            "job_id": "job-2",
            "images": [image],
            "content_list": [
                {
                    "type": "image",
                    "page_idx": 4,
                    "img_path": "images/figure-2.png",
                    "image_caption": [{"text": "部署拓扑图"}],
                    "bbox": [0, 50, 10, 60],
                },
                {
                    "type": "text",
                    "page_idx": 4,
                    "text": "这一页还有一段正文。",
                    "bbox": [100, 200, 150, 250],
                },
            ]
        }

    loader = MinerUPdfLoader(asset_root=tmp_path / "knowledge_assets", parser=fake_parser)
    documents = __import__("asyncio").run(loader.load(pdf_path))

    assert len(documents) == 1
    assert documents[0].metadata["related_asset_keys"] == ["image-0"]


def test_mineru_pdf_loader_merges_same_page_text_blocks(tmp_path):
    from app.ai.rag.ingest.loaders.mineru_pdf_loader import MinerUPdfLoader

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    def fake_parser(path: Path):
        return {
            "job_id": "job-merge",
            "images": [],
            "content_list": [
                {"type": "text", "page_idx": 1, "text": "Mengshu Sun"},
                {"type": "text", "page_idx": 1, "text": "Ant Group"},
                {"type": "text", "page_idx": 2, "text": "Abstract\nThis paper proposes..."},
            ],
        }

    loader = MinerUPdfLoader(asset_root=tmp_path / "knowledge_assets", parser=fake_parser)
    documents = __import__("asyncio").run(loader.load(pdf_path))

    assert len(documents) == 2
    assert documents[0].page_start == 1
    assert documents[0].content == "Mengshu Sun\n\nAnt Group"
    assert documents[1].page_start == 2


def test_mineru_pdf_loader_uses_precision_mode_when_token_is_available(monkeypatch, tmp_path):
    from app.ai.rag.ingest.loaders import mineru_pdf_loader
    from app.ai.rag.ingest.loaders.mineru_pdf_loader import MinerUPdfLoader

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    class FakeClient:
        def __init__(self):
            self.extract_called = False
            self.flash_called = False

        def extract(self, source, **kwargs):
            self.extract_called = True
            return SimpleNamespace(
                task_id="task-1",
                state="done",
                markdown="# 标题",
                content_list=[],
                images=[],
            )

        def flash_extract(self, source, **kwargs):
            self.flash_called = True
            raise AssertionError("flash_extract should not be called")

    client = FakeClient()
    monkeypatch.setattr(mineru_pdf_loader.settings, "MINERU_API_MODE", "precision")
    monkeypatch.setattr(mineru_pdf_loader.settings, "MINERU_TOKEN", "secret-token")

    loader = MinerUPdfLoader(asset_root=tmp_path / "knowledge_assets", client_factory=lambda token: client)
    parsed = loader._extract_with_sdk(pdf_path)

    assert client.extract_called is True
    assert parsed["job_id"] == "task-1"
    assert parsed["content_list"][0]["text"] == "# 标题"


def test_mineru_pdf_loader_falls_back_to_flash_without_token(monkeypatch, tmp_path):
    from app.ai.rag.ingest.loaders import mineru_pdf_loader
    from app.ai.rag.ingest.loaders.mineru_pdf_loader import MinerUPdfLoader

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    class FakeClient:
        def __init__(self):
            self.extract_called = False
            self.flash_called = False

        def extract(self, source, **kwargs):
            self.extract_called = True
            raise AssertionError("extract should not be called")

        def flash_extract(self, source, **kwargs):
            self.flash_called = True
            return SimpleNamespace(
                task_id="task-flash",
                state="done",
                markdown="flash markdown",
                content_list=[],
                images=[],
            )

    client = FakeClient()
    monkeypatch.setattr(mineru_pdf_loader.settings, "MINERU_API_MODE", "precision")
    monkeypatch.setattr(mineru_pdf_loader.settings, "MINERU_TOKEN", None)

    loader = MinerUPdfLoader(asset_root=tmp_path / "knowledge_assets", client_factory=lambda token: client)
    parsed = loader._extract_with_sdk(pdf_path)

    assert client.flash_called is True
    assert parsed["content_list"][0]["text"] == "flash markdown"


def test_persistence_service_marks_job_succeeded_and_inserts_milvus_payload():
    from app.ai.rag.ingest.models import IngestedChunk, IngestedDocument
    from app.ai.rag.ingest.persistence import PersistenceService

    class FakeSession:
        def __init__(self):
            self.added = []
            self.committed = 0
            self.rolled_back = 0

        def add(self, obj):
            self.added.append(obj)

        async def commit(self):
            self.committed += 1

        async def rollback(self):
            self.rolled_back += 1

    class FakeMilvus:
        def __init__(self):
            self.inserted = None
            self.collection_created = False

        def create_collection(self, drop_if_exists=False):
            self.collection_created = True

        def insert(self, data):
            self.inserted = data

    session = FakeSession()
    milvus = FakeMilvus()
    service = PersistenceService(session=session, milvus=milvus)

    document = IngestedDocument(
        source_path="data/sample.md",
        file_name="sample.md",
        file_type="md",
        content="正文内容",
        loader_name="langchain",
        metadata={},
    )
    chunk = IngestedChunk(
        chunk_id="chunk-1",
        source_path="data/sample.md",
        file_type="md",
        chunk_index=0,
        content="正文内容",
        metadata={},
    )

    __import__("asyncio").run(
        service.persist(
            source_path="data/sample.md",
            file_hash="hash-1",
            documents=[document],
            chunks=[chunk],
            embeddings={"chunk-1": [0.1, 0.2, 0.3]},
        )
    )

    job = next(obj for obj in session.added if isinstance(obj, IngestJob))

    assert session.committed == 1
    assert milvus.collection_created is True
    assert milvus.inserted[0]["chunk_id"] == "chunk-1"
    assert milvus.inserted[0]["document_id"]
    assert milvus.inserted[0]["vector_id"] == "vec_chunk-1"
    assert "content" not in milvus.inserted[0]
    assert job.started_at.tzinfo is None
    assert job.finished_at.tzinfo is None
    assert job.status == "succeeded"


def test_persistence_service_marks_job_failed_when_milvus_insert_raises():
    from app.ai.rag.ingest.models import IngestedChunk, IngestedDocument
    from app.ai.rag.ingest.persistence import PersistenceService

    class FakeSession:
        def __init__(self):
            self.added = []
            self.committed = 0
            self.rolled_back = 0

        def add(self, obj):
            self.added.append(obj)

        async def commit(self):
            self.committed += 1

        async def rollback(self):
            self.rolled_back += 1

    class BrokenMilvus:
        def create_collection(self, drop_if_exists=False):
            return None

        def insert(self, data):
            raise RuntimeError("milvus unavailable")

    session = FakeSession()
    service = PersistenceService(session=session, milvus=BrokenMilvus())

    document = IngestedDocument(
        source_path="data/sample.md",
        file_name="sample.md",
        file_type="md",
        content="正文内容",
        loader_name="langchain",
        metadata={},
    )
    chunk = IngestedChunk(
        chunk_id="chunk-1",
        source_path="data/sample.md",
        file_type="md",
        chunk_index=0,
        content="正文内容",
        metadata={},
    )

    try:
        __import__("asyncio").run(
            service.persist(
                source_path="data/sample.md",
                file_hash="hash-1",
                documents=[document],
                chunks=[chunk],
                embeddings={"chunk-1": [0.1, 0.2, 0.3]},
            )
        )
    except RuntimeError as exc:
        assert "milvus unavailable" in str(exc)
    else:
        raise AssertionError("Expected persist to propagate Milvus failure")

    job = next(obj for obj in session.added if isinstance(obj, IngestJob))

    assert session.rolled_back == 1
    assert job.status == "failed"
    assert "milvus unavailable" in job.error_message


def test_persistence_service_compensates_milvus_when_commit_fails():
    from app.ai.rag.ingest.models import IngestedChunk, IngestedDocument
    from app.ai.rag.ingest.persistence import PersistenceService

    class FakeSession:
        def __init__(self):
            self.added = []
            self.rolled_back = 0

        def add(self, obj):
            self.added.append(obj)

        async def commit(self):
            raise RuntimeError("commit failed")

        async def rollback(self):
            self.rolled_back += 1

    class FakeMilvus:
        def __init__(self):
            self.deleted_expr = None

        def create_collection(self, drop_if_exists=False):
            return None

        def insert(self, data):
            return None

        def delete(self, expr):
            self.deleted_expr = expr

    session = FakeSession()
    milvus = FakeMilvus()
    service = PersistenceService(session=session, milvus=milvus)

    document = IngestedDocument(
        source_path="data/sample.md",
        file_name="sample.md",
        file_type="md",
        content="正文内容",
        loader_name="langchain",
        metadata={},
    )
    chunk = IngestedChunk(
        chunk_id="chunk-1",
        source_path="data/sample.md",
        file_type="md",
        chunk_index=0,
        content="正文内容",
        metadata={},
    )

    try:
        __import__("asyncio").run(
            service.persist(
                source_path="data/sample.md",
                file_hash="hash-1",
                documents=[document],
                chunks=[chunk],
                embeddings={"chunk-1": [0.1, 0.2, 0.3]},
            )
        )
    except RuntimeError as exc:
        assert "commit failed" in str(exc)
    else:
        raise AssertionError("Expected persist to propagate commit failure")

    assert session.rolled_back == 1
    assert milvus.deleted_expr == 'vector_id in ["vec_chunk-1"]'


def test_persistence_service_truncates_preview_text_by_utf8_bytes():
    from app.ai.rag.ingest.persistence import PersistenceService

    text = "中" * 400
    truncated = PersistenceService._truncate_utf8(text, 500)

    assert len(truncated.encode("utf-8")) <= 500
    assert truncated
