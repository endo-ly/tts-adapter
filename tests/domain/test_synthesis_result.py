"""Tests for SynthesisResult value object."""

import pytest
from pydantic import ValidationError

from app.domain.value_objects.synthesis_result import SynthesisResult


class TestSynthesisResult:
    def test_valid_result(self):
        result = SynthesisResult(audio_bytes=b"RIFF\x00\x00\x00\x00")
        assert result.audio_bytes.startswith(b"RIFF")

    def test_default_media_type(self):
        result = SynthesisResult(audio_bytes=b"data")
        assert result.media_type == "audio/wav"

    def test_default_format(self):
        result = SynthesisResult(audio_bytes=b"data")
        assert result.format == "wav"

    def test_media_type_only_wav(self):
        with pytest.raises(ValidationError):
            SynthesisResult(audio_bytes=b"data", media_type="audio/mp3")

    def test_format_only_wav(self):
        with pytest.raises(ValidationError):
            SynthesisResult(audio_bytes=b"data", format="mp3")

    def test_explicit_wav_values(self):
        result = SynthesisResult(
            audio_bytes=b"data",
            media_type="audio/wav",
            format="wav",
        )
        assert result.media_type == "audio/wav"
        assert result.format == "wav"
