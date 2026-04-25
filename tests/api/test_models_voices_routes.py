"""Tests for models and voices routes."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestModelsRoute:
    async def test_get_models_returns_list(self, client):
        resp = await client.get("/v1/models")
        assert resp.status_code == 200
        body = resp.json()
        assert body["object"] == "list"
        assert len(body["data"]) >= 1
        ids = [m["id"] for m in body["data"]]
        assert "tts-default" in ids


class TestVoicesRoute:
    async def test_get_voices_returns_list(self, client):
        resp = await client.get("/v1/voices")
        assert resp.status_code == 200
        body = resp.json()
        assert body["object"] == "list"
        assert len(body["data"]) >= 1
        ids = [v["id"] for v in body["data"]]
        assert "egopulse" in ids
