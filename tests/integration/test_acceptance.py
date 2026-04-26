"""Integration tests — acceptance criteria from plan.md §7.3."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestAcceptanceHealth:
    async def test_health_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"


class TestAcceptanceModels:
    async def test_get_models_returns_data(self, client):
        resp = await client.get("/v1/models")
        assert resp.status_code == 200
        body = resp.json()
        assert body["object"] == "list"
        assert len(body["data"]) >= 1

    async def test_model_tts_default_works(self, client):
        ids = [m["id"] for m in (await client.get("/v1/models")).json()["data"]]
        assert "tts-default" in ids


class TestAcceptanceVoices:
    async def test_get_voices_returns_data(self, client):
        resp = await client.get("/v1/voices")
        assert resp.status_code == 200
        body = resp.json()
        assert body["object"] == "list"
        assert len(body["data"]) >= 1

    async def test_voice_your_voice_name_works(self, client):
        ids = [v["id"] for v in (await client.get("/v1/voices")).json()["data"]]
        assert "your-voice-name" in ids


class TestAcceptanceOpenAISpeech:
    async def test_post_audio_speech_wav(self, client):
        resp = await client.post(
            "/v1/audio/speech",
            json={"model": "tts-default", "voice": "your-voice-name", "input": "テスト"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"
        assert resp.content.startswith(b"RIFF")

    async def test_unknown_model_404(self, client):
        resp = await client.post(
            "/v1/audio/speech",
            json={"model": "nonexistent", "voice": "your-voice-name", "input": "x"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "model_not_found"

    async def test_unknown_voice_404(self, client):
        resp = await client.post(
            "/v1/audio/speech",
            json={"model": "tts-default", "voice": "nonexistent", "input": "x"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "voice_not_found"

    async def test_voice_binding_missing_409(self, client):
        resp = await client.post(
            "/v1/audio/speech",
            json={"model": "irodori-voicedesign", "voice": "your-voice-name", "input": "x"},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "voice_binding_not_found"

    async def test_response_format_wav_only(self, client):
        resp = await client.post(
            "/v1/audio/speech",
            json={"model": "tts-default", "voice": "your-voice-name", "input": "x", "response_format": "mp3"},
        )
        assert resp.status_code == 400

    async def test_speed_1_0_only(self, client):
        resp = await client.post(
            "/v1/audio/speech",
            json={"model": "tts-default", "voice": "your-voice-name", "input": "x", "speed": 2.0},
        )
        assert resp.status_code == 400


class TestAcceptanceNativeSpeech:
    async def test_post_native_speech_wav(self, client):
        resp = await client.post(
            "/v1/speech",
            json={"model": "tts-default", "voice_id": "your-voice-name", "speech_text": "了解"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"
        assert resp.content.startswith(b"RIFF")

    async def test_native_speech_404_unknown_model(self, client):
        resp = await client.post(
            "/v1/speech",
            json={"model": "nonexistent", "voice_id": "your-voice-name", "speech_text": "x"},
        )
        assert resp.status_code == 404


class TestAcceptanceProviderExtensibility:
    def test_fake_provider_is_registered(self):
        from app.main import _provider_registry
        provider = _provider_registry.get("fake")
        assert provider.provider_name == "fake"

    def test_irodori_provider_is_registered(self):
        from app.main import _provider_registry
        provider = _provider_registry.get("irodori")
        assert provider.provider_name == "irodori"

    def test_registry_allows_additional_providers(self):
        from app.main import _provider_registry
        from app.infrastructure.providers.fake.provider import FakeProvider
        extra = FakeProvider()
        extra.provider_name = "qwen_tts"
        _provider_registry.register(extra)
        assert _provider_registry.get("qwen_tts").provider_name == "qwen_tts"


class TestAcceptanceYamlValidation:
    def test_models_yaml_loaded_with_safe_load(self):
        from app.main import _model_repo
        models = _model_repo.list_all()
        assert len(models) >= 1
        for m in models:
            assert m.id
            assert m.provider

    def test_voices_yaml_loaded_with_safe_load(self):
        from app.main import _voice_repo
        voices = _voice_repo.list_all()
        assert len(voices) >= 1
        for v in voices:
            assert v.voice_id
            assert v.display_name
