"""Fake TTS provider for testing and development."""

from app.domain.value_objects.synthesis_request import ProviderSynthesisRequest
from app.domain.value_objects.synthesis_result import SynthesisResult


class FakeProvider:
    provider_name: str = "fake"

    async def synthesize(
        self, request: ProviderSynthesisRequest
    ) -> SynthesisResult:
        # Minimal valid WAV: 44-byte header + silence
        # RIFF header for 8-bit mono PCM, 8000 Hz, 0 data bytes
        wav = (
            b"RIFF"
            b"\x24\x00\x00\x00"  # file size - 8
            b"WAVE"
            b"fmt "
            b"\x10\x00\x00\x00"  # chunk size
            b"\x01\x00"          # PCM format
            b"\x01\x00"          # mono
            b"\x40\x1f\x00\x00"  # 8000 Hz sample rate
            b"\x40\x1f\x00\x00"  # byte rate
            b"\x01\x00"          # block align
            b"\x08\x00"          # bits per sample
            b"data"
            b"\x00\x00\x00\x00"  # data size = 0
        )
        return SynthesisResult(audio_bytes=wav)
