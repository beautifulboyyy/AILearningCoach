"""refactor knowledge ingest schema

Revision ID: 4d5e6f7a8b9c
Revises: 3c4d5e6f7a8b
Create Date: 2026-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4d5e6f7a8b9c"
down_revision = "3c4d5e6f7a8b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(op.f("ix_knowledge_chunks_lecture_number"), table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_vector_id"), table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_path", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("loader_name", sa.String(length=100), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("meta_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_documents_id"), "knowledge_documents", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_source_path"), "knowledge_documents", ["source_path"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_file_type"), "knowledge_documents", ["file_type"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_file_hash"), "knowledge_documents", ["file_hash"], unique=False)

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("vector_id", sa.String(length=100), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("meta_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_chunks_id"), "knowledge_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_document_id"), "knowledge_chunks", ["document_id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_vector_id"), "knowledge_chunks", ["vector_id"], unique=True)

    op.create_table(
        "knowledge_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("page_idx", sa.Integer(), nullable=True),
        sa.Column("asset_path", sa.String(length=500), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("meta_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_assets_id"), "knowledge_assets", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_assets_document_id"), "knowledge_assets", ["document_id"], unique=False)
    op.create_index(op.f("ix_knowledge_assets_asset_type"), "knowledge_assets", ["asset_type"], unique=False)

    op.create_table(
        "knowledge_chunk_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("chunk_id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=36), nullable=False),
        sa.Column("relation_type", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meta_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["knowledge_assets.id"]),
        sa.ForeignKeyConstraint(["chunk_id"], ["knowledge_chunks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_chunk_assets_id"), "knowledge_chunk_assets", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunk_assets_chunk_id"), "knowledge_chunk_assets", ["chunk_id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunk_assets_asset_id"), "knowledge_chunk_assets", ["asset_id"], unique=False)

    op.create_table(
        "ingest_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_path", sa.String(length=500), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("meta_info", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingest_jobs_id"), "ingest_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_ingest_jobs_source_path"), "ingest_jobs", ["source_path"], unique=False)
    op.create_index(op.f("ix_ingest_jobs_file_hash"), "ingest_jobs", ["file_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ingest_jobs_file_hash"), table_name="ingest_jobs")
    op.drop_index(op.f("ix_ingest_jobs_source_path"), table_name="ingest_jobs")
    op.drop_index(op.f("ix_ingest_jobs_id"), table_name="ingest_jobs")
    op.drop_table("ingest_jobs")

    op.drop_index(op.f("ix_knowledge_chunk_assets_asset_id"), table_name="knowledge_chunk_assets")
    op.drop_index(op.f("ix_knowledge_chunk_assets_chunk_id"), table_name="knowledge_chunk_assets")
    op.drop_index(op.f("ix_knowledge_chunk_assets_id"), table_name="knowledge_chunk_assets")
    op.drop_table("knowledge_chunk_assets")

    op.drop_index(op.f("ix_knowledge_assets_asset_type"), table_name="knowledge_assets")
    op.drop_index(op.f("ix_knowledge_assets_document_id"), table_name="knowledge_assets")
    op.drop_index(op.f("ix_knowledge_assets_id"), table_name="knowledge_assets")
    op.drop_table("knowledge_assets")

    op.drop_index(op.f("ix_knowledge_chunks_vector_id"), table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_document_id"), table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_id"), table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    op.drop_index(op.f("ix_knowledge_documents_file_hash"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_file_type"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_source_path"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_id"), table_name="knowledge_documents")
    op.drop_table("knowledge_documents")

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lecture_number", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(length=50), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("vector_id", sa.String(length=100), nullable=True),
        sa.Column("meta_info", sa.JSON(), nullable=True),
        sa.Column("difficulty_level", sa.Enum("BEGINNER", "INTERMEDIATE", "ADVANCED", name="difficultylevel"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_chunks_id"), "knowledge_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_lecture_number"), "knowledge_chunks", ["lecture_number"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_vector_id"), "knowledge_chunks", ["vector_id"], unique=True)
