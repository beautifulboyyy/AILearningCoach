import os
import importlib

os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "learning_coach")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("MILVUS_HOST", "localhost")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("DASHSCOPE_API_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "test-secret")

milvus_module = importlib.import_module("app.ai.rag.milvus_client")
from app.ai.rag.milvus_client import MilvusClient


def test_milvus_client_insert_creates_collection_when_missing(monkeypatch):
    calls = {"has": 0, "created": 0, "inserted": 0}

    class FakeCollection:
        def __init__(self, name=None, schema=None):
            self.name = name
            self.schema = schema

        def create_index(self, field_name, index_params):
            return None

        def insert(self, rows):
            calls["inserted"] += 1

        def flush(self):
            return None

    client = MilvusClient()
    monkeypatch.setattr(milvus_module.connections, "connect", lambda alias, host, port: None)

    def fake_has_collection(name):
        calls["has"] += 1
        return calls["created"] > 0

    monkeypatch.setattr(milvus_module.utility, "has_collection", fake_has_collection)
    monkeypatch.setattr(milvus_module, "Collection", FakeCollection)

    original_create_collection = client.create_collection

    def tracked_create_collection(drop_if_exists=False):
        calls["created"] += 1
        return original_create_collection(drop_if_exists=drop_if_exists)

    client.create_collection = tracked_create_collection

    client.insert(
        [
            {
                "vector_id": "vec-1",
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "preview_text": "preview",
                "file_type": "md",
                "page_idx": 1,
                "embedding": [0.1] * 1024,
                "metadata": {},
            }
        ]
    )

    assert calls["created"] >= 1
    assert calls["inserted"] == 1
