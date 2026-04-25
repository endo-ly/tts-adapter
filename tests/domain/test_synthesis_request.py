"""Tests for ProviderSynthesisRequest value object."""

import pytest
from pydantic import ValidationError

from app.domain.value_objects.synthesis_request import ProviderSynthesisRequest


class TestProviderSynthesisRequest:
    def test_valid_request(self):
        req = ProviderSynthesisRequest(
            model_id="tts-default",
            voice_id="egopulse",
            text="こんにちは",
            provider="irodori",
            engine="base",
            provider_config={"seed": 42},
        )
        assert req.text == "こんにちは"
        assert req.model_id == "tts-default"

    def test_text_min_length_1(self):
        with pytest.raises(ValidationError):
            ProviderSynthesisRequest(
                model_id="tts-default",
                voice_id="egopulse",
                text="",
                provider="fake",
                engine="base",
                provider_config={},
            )

    def test_text_cannot_be_none(self):
        with pytest.raises(ValidationError):
            ProviderSynthesisRequest(
                model_id="tts-default",
                voice_id="egopulse",
                text=None,  # type: ignore
                provider="fake",
                engine="base",
                provider_config={},
            )

    def test_response_format_wav_only(self):
        req = ProviderSynthesisRequest(
            model_id="tts-default",
            voice_id="egopulse",
            text="test",
            response_format="wav",
            provider="fake",
            engine="base",
            provider_config={},
        )
        assert req.response_format == "wav"

    def test_response_format_non_wav_rejected(self):
        with pytest.raises(ValidationError):
            ProviderSynthesisRequest(
                model_id="tts-default",
                voice_id="egopulse",
                text="test",
                response_format="mp3",
                provider="fake",
                engine="base",
                provider_config={},
            )

    def test_default_speed_is_1(self):
        req = ProviderSynthesisRequest(
            model_id="tts-default",
            voice_id="egopulse",
            text="test",
            provider="fake",
            engine="base",
            provider_config={},
        )
        assert req.speed == 1.0

    def test_provider_config_is_dict(self):
        req = ProviderSynthesisRequest(
            model_id="tts-default",
            voice_id="egopulse",
            text="test",
            provider="fake",
            engine="base",
            provider_config={"checkpoint": "x", "seed": 42},
        )
        assert req.provider_config["seed"] == 42
