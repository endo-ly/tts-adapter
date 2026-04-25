"""Tests for FakeProvider."""

from app.domain.value_objects.synthesis_request import ProviderSynthesisRequest
from app.domain.value_objects.synthesis_result import SynthesisResult
from app.infrastructure.providers.fake.provider import FakeProvider


def _make_request() -> ProviderSynthesisRequest:
    return ProviderSynthesisRequest(
        model_id="tts-default",
        voice_id="egopulse",
        text="テスト",
        provider="fake",
        engine="base",
        provider_config={},
    )


class TestFakeProvider:
    def test_provider_name(self):
        p = FakeProvider()
        assert p.provider_name == "fake"

    async def test_synthesize_returns_synthesis_result(self):
        p = FakeProvider()
        result = await p.synthesize(_make_request())
        assert isinstance(result, SynthesisResult)

    async def test_synthesize_returns_wav_bytes(self):
        p = FakeProvider()
        result = await p.synthesize(_make_request())
        assert result.audio_bytes.startswith(b"RIFF")
        assert result.media_type == "audio/wav"
        assert result.format == "wav"

    async def test_synthesize_returns_nonzero_bytes(self):
        p = FakeProvider()
        result = await p.synthesize(_make_request())
        assert len(result.audio_bytes) > 0
