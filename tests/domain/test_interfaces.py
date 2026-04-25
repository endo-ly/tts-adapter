"""Tests for domain interface protocols."""

from typing import Any

from app.domain.interfaces.model_profile_repository import ModelProfileRepository
from app.domain.interfaces.tts_provider import TTSProvider
from app.domain.interfaces.voice_profile_repository import VoiceProfileRepository
from app.domain.value_objects.synthesis_request import ProviderSynthesisRequest
from app.domain.value_objects.synthesis_result import SynthesisResult


class FakeProvider:
    """Minimal concrete class to test TTSProvider protocol."""

    provider_name: str = "fake"

    async def synthesize(self, request: ProviderSynthesisRequest) -> SynthesisResult:
        return SynthesisResult(audio_bytes=b"fake")


class FakeModelRepo:
    """Minimal concrete class to test ModelProfileRepository protocol."""

    async def get_by_id(self, model_id: str) -> Any:
        return None

    async def list_all(self) -> list:
        return []


class FakeVoiceRepo:
    """Minimal concrete class to test VoiceProfileRepository protocol."""

    async def get_by_id(self, voice_id: str) -> Any:
        return None

    async def list_all(self) -> list:
        return []


class TestTTSProviderProtocol:
    def test_concrete_class_satisfies_protocol(self):
        provider = FakeProvider()
        assert isinstance(provider, TTSProvider)

    def test_provider_name_accessible(self):
        provider = FakeProvider()
        assert provider.provider_name == "fake"

    async def test_concrete_synthesize_returns_result(self):
        provider = FakeProvider()
        req = ProviderSynthesisRequest(
            model_id="tts-default",
            voice_id="egopulse",
            text="test",
            provider="fake",
            engine="base",
            provider_config={},
        )
        result = await provider.synthesize(req)
        assert isinstance(result, SynthesisResult)


class TestModelProfileRepositoryProtocol:
    def test_has_get_by_id(self):
        assert hasattr(ModelProfileRepository, "get_by_id")

    def test_has_list_all(self):
        assert hasattr(ModelProfileRepository, "list_all")

    def test_concrete_class_satisfies_protocol(self):
        repo = FakeModelRepo()
        assert isinstance(repo, ModelProfileRepository)


class TestVoiceProfileRepositoryProtocol:
    def test_has_get_by_id(self):
        assert hasattr(VoiceProfileRepository, "get_by_id")

    def test_has_list_all(self):
        assert hasattr(VoiceProfileRepository, "list_all")

    def test_concrete_class_satisfies_protocol(self):
        repo = FakeVoiceRepo()
        assert isinstance(repo, VoiceProfileRepository)
