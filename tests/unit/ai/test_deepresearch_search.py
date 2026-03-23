import pytest

from app.ai.deepresearch.search import BochaSearchClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeAsyncClient:
    def __init__(self, payload):
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers=None, json=None):
        return FakeResponse(self.payload)


@pytest.mark.asyncio
async def test_bocha_search_client_reads_nested_data_payload(monkeypatch):
    import app.ai.deepresearch.search as search_module

    payload = {
        "code": 200,
        "data": {
            "webPages": {
                "value": [
                    {
                        "name": "博查结果",
                        "url": "https://example.com/result",
                        "summary": "这是摘要",
                        "siteName": "Example",
                    }
                ]
            }
        },
    }

    monkeypatch.setattr(
        search_module.httpx,
        "AsyncClient",
        lambda timeout=30.0: FakeAsyncClient(payload),
    )

    client = BochaSearchClient(api_key="test-key")
    results = await client.search("AI learning coach")

    assert len(results) == 1
    assert results[0]["provider"] == "bocha"
    assert results[0]["title"] == "博查结果"
    assert results[0]["content"] == "这是摘要"
