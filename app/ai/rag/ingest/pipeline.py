"""
离线导入主流程
"""
from hashlib import sha256
from pathlib import Path

from app.ai.rag.embeddings import embedding_model
from app.ai.rag.ingest.loaders.langchain_loader import LangChainDocumentLoader
from app.ai.rag.ingest.loaders.mineru_pdf_loader import MinerUPdfLoader
from app.ai.rag.ingest.persistence import PersistenceService
from app.ai.rag.ingest.registry import LoaderRegistry
from app.ai.rag.ingest.splitter import DocumentSplitter
from app.ai.rag.milvus_client import milvus_client
from app.db.session import async_session_maker
from app.utils.logger import app_logger


class IngestPipeline:
    """统一离线导入流程"""

    def __init__(self, asset_root: Path | None = None):
        self.registry = LoaderRegistry()
        self.registry.register(LangChainDocumentLoader())
        self.registry.register(MinerUPdfLoader(asset_root=asset_root))
        self.splitter = DocumentSplitter()

    async def ingest_directory(self, data_dir: str) -> None:
        data_path = Path(data_dir)
        if not data_path.exists():
            raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

        candidate_files = [
            path
            for path in data_path.iterdir()
            if path.is_file() and path.suffix.lower() in {".txt", ".docx", ".md", ".pdf"}
        ]

        if not candidate_files:
            app_logger.warning(f"No supported files found in: {data_dir}")
            return

        async with async_session_maker() as session:
            persistence = PersistenceService(session=session, milvus=milvus_client)
            for file_path in candidate_files:
                try:
                    await self.ingest_file(file_path, persistence)
                except Exception as exc:
                    app_logger.error(f"Failed to ingest file {file_path}: {exc}")

    async def ingest_file(self, file_path: Path, persistence: PersistenceService) -> None:
        source_path = self.normalize_source_path(file_path)
        file_hash = self.compute_file_hash(file_path)

        loader = self.registry.get_loader(file_path)
        documents = await loader.load(file_path)
        chunks = self.splitter.split_documents(documents)
        embeddings = await embedding_model.embed_texts([chunk.content for chunk in chunks])
        embeddings_by_chunk = {
            chunk.chunk_id: embedding
            for chunk, embedding in zip(chunks, embeddings)
        }

        await persistence.persist(
            source_path=source_path,
            file_hash=file_hash,
            documents=documents,
            chunks=chunks,
            embeddings=embeddings_by_chunk,
        )
        app_logger.info(f"Ingested file: {source_path}")

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        return sha256(file_path.read_bytes()).hexdigest()

    @staticmethod
    def normalize_source_path(file_path: Path) -> str:
        cwd = Path.cwd().resolve()
        resolved = file_path.resolve()
        try:
            return str(resolved.relative_to(cwd)).replace("\\", "/")
        except ValueError:
            return str(resolved).replace("\\", "/")
