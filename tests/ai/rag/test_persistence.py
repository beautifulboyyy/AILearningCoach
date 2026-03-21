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

    images_dir = tmp_path / "mineru-output" / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "figure-1.png").write_bytes(b"image")

    def fake_parser(path: Path):
        return {
            "job_id": "job-1",
            "content_list": [
                {
                    "type": "image",
                    "page_idx": 2,
                    "img_path": str(images_dir / "figure-1.png"),
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

    images_dir = tmp_path / "mineru-output" / "images"
    images_dir.mkdir(parents=True)
    (images_dir / "figure-2.png").write_bytes(b"image")

    def fake_parser(path: Path):
        return {
            "job_id": "job-2",
            "content_list": [
                {
                    "type": "image",
                    "page_idx": 4,
                    "img_path": str(images_dir / "figure-2.png"),
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
