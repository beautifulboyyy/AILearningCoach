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

from app.ai.rag.generator import RAGGenerator
from app.ai.rag.retriever import RAGRetriever


class FakeEmbedding:
    async def embed_query(self, query: str):
        return [0.1, 0.2, 0.3]


class FakeMilvus:
    def search(self, query_embedding, top_k, filter_expr=None):
        return [
            {
                "vector_id": "vec_chunk-1",
                "chunk_id": "chunk-1",
                "document_id": "doc-1",
                "preview_text": "这是摘要",
                "distance": 0.91,
                "metadata": {},
            }
        ]


async def fake_fetcher(chunk_ids):
    assert chunk_ids == ["chunk-1"]
    return {
        "chunk-1": {
            "content": "这是正文内容",
            "document_name": "sample.pdf",
            "file_type": "pdf",
            "page": 3,
            "source_path": "data/sample.pdf",
            "assets": [
                {
                    "asset_type": "image",
                    "asset_path": "sample/job-1/figure-1.png",
                    "caption": "系统架构图",
                }
            ],
        }
    }


def test_retriever_returns_hydrated_citations():
    retriever = RAGRetriever(
        milvus=FakeMilvus(),
        embedding=FakeEmbedding(),
        citation_fetcher=fake_fetcher,
    )

    results = __import__("asyncio").run(retriever.retrieve("什么是 RAG", top_k=1))

    assert len(results) == 1
    assert results[0]["content"] == "这是正文内容"
    assert results[0]["source"]["document_name"] == "sample.pdf"
    assert results[0]["source"]["page"] == 3
    assert results[0]["source"]["assets"][0]["caption"] == "系统架构图"


def test_generator_extracts_new_source_structure():
    generator = RAGGenerator()
    sources = generator._extract_sources(
        [
            {
                "source": {
                    "document_name": "sample.pdf",
                    "file_type": "pdf",
                    "page": 3,
                    "source_path": "data/sample.pdf",
                    "assets": [],
                }
            }
        ]
    )

    assert sources == [
        {
            "document_name": "sample.pdf",
            "file_type": "pdf",
            "page": 3,
            "source_path": "data/sample.pdf",
            "assets": [],
            "text": "sample.pdf (p.3)",
        }
    ]
