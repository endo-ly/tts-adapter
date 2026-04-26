"""Tests for Native speech route."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestNativeSpeechRoute:
    async def test_post_native_speech_returns_wav(self, client):
        resp = await client.post(
            "/v1/speech",
            json={
                "model": "tts-default",
                "voice_id": "your-voice-name",
                "speech_text": "了解しました",
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"
        assert resp.content.startswith(b"RIFF")

    async def test_post_native_speech_404_unknown_model(self, client):
        resp = await client.post(
            "/v1/speech",
            json={
                "model": "nonexistent",
                "voice_id": "your-voice-name",
                "speech_text": "test",
            },
        )
        assert resp.status_code == 404

    async def test_post_native_speech_accepts_style_hints_ignored(self, client):
        resp = await client.post(
            "/v1/speech",
            json={
                "model": "tts-default",
                "voice_id": "your-voice-name",
                "speech_text": "test",
                "style_hints": {"emotion": "gentle", "energy": 0.3},
            },
        )
        assert resp.status_code == 200
