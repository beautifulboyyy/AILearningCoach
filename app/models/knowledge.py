"""
通用知识摄取模型
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base, TimestampMixin


class KnowledgeDocument(Base, TimestampMixin):
    """知识文档表"""

    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, index=True)
    source_path = Column(String(500), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False, index=True)
    loader_name = Column(String(100), nullable=False)
    file_hash = Column(String(128), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="processing")
    meta_info = Column(JSON, nullable=True)

    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    assets = relationship(
        "KnowledgeAsset",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, file_name={self.file_name}, file_type={self.file_type})>"


class KnowledgeChunk(Base, TimestampMixin):
    """知识块表"""

    __tablename__ = "knowledge_chunks"

    id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("knowledge_documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    vector_id = Column(String(100), nullable=True, unique=True, index=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    meta_info = Column(JSON, nullable=True)

    document = relationship("KnowledgeDocument", back_populates="chunks")
    asset_links = relationship(
        "KnowledgeChunkAsset",
        back_populates="chunk",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<KnowledgeChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"


class KnowledgeAsset(Base, TimestampMixin):
    """知识资产表，第一版重点用于图片资源"""

    __tablename__ = "knowledge_assets"

    id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("knowledge_documents.id"), nullable=False, index=True)
    asset_type = Column(String(50), nullable=False, index=True)
    page_idx = Column(Integer, nullable=True)
    asset_path = Column(String(500), nullable=False)
    caption = Column(Text, nullable=True)
    meta_info = Column(JSON, nullable=True)

    document = relationship("KnowledgeDocument", back_populates="assets")
    chunk_links = relationship(
        "KnowledgeChunkAsset",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<KnowledgeAsset(id={self.id}, document_id={self.document_id}, asset_type={self.asset_type})>"


class KnowledgeChunkAsset(Base, TimestampMixin):
    """知识块与资产关系表"""

    __tablename__ = "knowledge_chunk_assets"

    id = Column(String(36), primary_key=True, index=True)
    chunk_id = Column(String(36), ForeignKey("knowledge_chunks.id"), nullable=False, index=True)
    asset_id = Column(String(36), ForeignKey("knowledge_assets.id"), nullable=False, index=True)
    relation_type = Column(String(50), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    meta_info = Column(JSON, nullable=True)

    chunk = relationship("KnowledgeChunk", back_populates="asset_links")
    asset = relationship("KnowledgeAsset", back_populates="chunk_links")

    def __repr__(self):
        return f"<KnowledgeChunkAsset(id={self.id}, chunk_id={self.chunk_id}, asset_id={self.asset_id})>"


class IngestJob(Base, TimestampMixin):
    """离线导入任务表"""

    __tablename__ = "ingest_jobs"

    id = Column(String(36), primary_key=True, index=True)
    source_path = Column(String(500), nullable=False, index=True)
    file_hash = Column(String(128), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="running")
    error_message = Column(Text, nullable=True)
    meta_info = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<IngestJob(id={self.id}, source_path={self.source_path}, status={self.status})>"
