"""
离线导入持久化服务
"""
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, select

from app.ai.rag.ingest.models import IngestedChunk, IngestedDocument
from app.models.knowledge import (
    IngestJob,
    KnowledgeAsset,
    KnowledgeChunk,
    KnowledgeChunkAsset,
    KnowledgeDocument,
)


class PersistenceService:
    """负责 PostgreSQL 与 Milvus 的离线持久化编排"""

    def __init__(self, session, milvus):
        self.session = session
        self.milvus = milvus

    async def persist(
        self,
        source_path: str,
        file_hash: str,
        documents: list[IngestedDocument],
        chunks: list[IngestedChunk],
        embeddings: dict[str, list[float]],
    ) -> IngestJob:
        job = IngestJob(
            id=str(uuid4()),
            source_path=source_path,
            file_hash=file_hash,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(job)

        try:
            await self.cleanup_existing(source_path)

            if not documents:
                raise ValueError(f"No parsed documents for source: {source_path}")

            primary_document = documents[0]
            knowledge_document = KnowledgeDocument(
                id=str(uuid4()),
                source_path=source_path,
                file_name=primary_document.file_name,
                file_type=primary_document.file_type,
                loader_name=primary_document.loader_name,
                file_hash=file_hash,
                status="processed",
                meta_info=self._merge_document_metadata(documents),
            )
            self.session.add(knowledge_document)

            asset_id_by_key = {}
            for asset in self._collect_unique_assets(documents):
                asset_id = str(uuid4())
                asset_id_by_key[asset.asset_key] = asset_id
                self.session.add(
                    KnowledgeAsset(
                        id=asset_id,
                        document_id=knowledge_document.id,
                        asset_type=asset.asset_type,
                        page_idx=asset.page_idx,
                        asset_path=asset.asset_path,
                        caption=asset.caption,
                        meta_info=asset.metadata,
                    )
                )

            milvus_payload = []
            for chunk in chunks:
                vector_id = f"vec_{chunk.chunk_id}"
                self.session.add(
                    KnowledgeChunk(
                        id=chunk.chunk_id,
                        document_id=knowledge_document.id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        vector_id=vector_id,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        meta_info=chunk.metadata,
                    )
                )

                for sort_order, asset_key in enumerate(chunk.related_asset_keys):
                    asset_id = asset_id_by_key.get(asset_key)
                    if asset_id is None:
                        continue
                    self.session.add(
                        KnowledgeChunkAsset(
                            id=str(uuid4()),
                            chunk_id=chunk.chunk_id,
                            asset_id=asset_id,
                            relation_type="adjacent",
                            sort_order=sort_order,
                            meta_info={},
                        )
                    )

                milvus_payload.append(
                    {
                        "vector_id": vector_id,
                        "chunk_id": chunk.chunk_id,
                        "document_id": knowledge_document.id,
                        "preview_text": chunk.content[:500],
                        "content": chunk.content[:8000],
                        "file_type": chunk.file_type,
                        "page_idx": chunk.page_start,
                        "embedding": embeddings[chunk.chunk_id],
                        "metadata": chunk.metadata,
                    }
                )

            self.milvus.create_collection(drop_if_exists=False)
            self.milvus.insert(milvus_payload)

            job.status = "succeeded"
            job.finished_at = datetime.now(timezone.utc)
            await self.session.commit()
            return job
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = datetime.now(timezone.utc)
            await self.session.rollback()
            raise

    async def cleanup_existing(self, source_path: str) -> None:
        if not hasattr(self.session, "execute"):
            return

        result = await self.session.execute(
            select(KnowledgeDocument.id).where(KnowledgeDocument.source_path == source_path)
        )
        document_ids = list(result.scalars().all())
        if not document_ids:
            return

        vector_result = await self.session.execute(
            select(KnowledgeChunk.vector_id).where(KnowledgeChunk.document_id.in_(document_ids))
        )
        vector_ids = [vector_id for vector_id in vector_result.scalars().all() if vector_id]
        if vector_ids:
            quoted_ids = ", ".join(f'"{vector_id}"' for vector_id in vector_ids)
            self.milvus.delete(f"vector_id in [{quoted_ids}]")

        await self.session.execute(
            delete(KnowledgeChunkAsset).where(
                KnowledgeChunkAsset.chunk_id.in_(
                    select(KnowledgeChunk.id).where(KnowledgeChunk.document_id.in_(document_ids))
                )
            )
        )
        await self.session.execute(delete(KnowledgeAsset).where(KnowledgeAsset.document_id.in_(document_ids)))
        await self.session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id.in_(document_ids)))
        await self.session.execute(delete(KnowledgeDocument).where(KnowledgeDocument.id.in_(document_ids)))

        self._cleanup_asset_directory(source_path)

    @staticmethod
    def _collect_unique_assets(documents: list[IngestedDocument]):
        seen = set()
        assets = []
        for document in documents:
            for asset in document.assets:
                if asset.asset_key in seen:
                    continue
                seen.add(asset.asset_key)
                assets.append(asset)
        return assets

    @staticmethod
    def _merge_document_metadata(documents: list[IngestedDocument]) -> dict:
        merged = {}
        for document in documents:
            merged.update(document.metadata)
        return merged

    @staticmethod
    def _cleanup_asset_directory(source_path: str) -> None:
        stem = Path(source_path).stem
        candidate = Path("data/knowledge_assets") / stem
        if candidate.exists():
            import shutil

            shutil.rmtree(candidate, ignore_errors=True)
