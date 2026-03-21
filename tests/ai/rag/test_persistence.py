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
