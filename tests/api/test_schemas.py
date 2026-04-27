"""Tests for API schemas."""

import pytest
from pydantic import ValidationError

from app.api.schemas.openai_speech import OpenAISpeechRequest
from app.api.schemas.native_speech import NativeSpeechRequest
from app.api.schemas.error import ErrorDetail, ErrorResponse


class TestOpenAISpeechRequest:
    def test_valid_request(self):
        req = OpenAISpeechRequest(model="tts-default", voice="egopulse", input="hello")
        assert req.model == "tts-default"

    def test_missing_model_raises(self):
        with pytest.raises(ValidationError):
            OpenAISpeechRequest(voice="egopulse", input="hello")

    def test_missing_voice_raises(self):
        with pytest.raises(ValidationError):
            OpenAISpeechRequest(model="tts-default", input="hello")

    def test_missing_input_raises(self):
        with pytest.raises(ValidationError):
            OpenAISpeechRequest(model="tts-default", voice="egopulse")

    def test_empty_input_raises(self):
        with pytest.raises(ValidationError):
            OpenAISpeechRequest(model="tts-default", voice="egopulse", input="")

    def test_default_format_is_wav(self):
        req = OpenAISpeechRequest(model="tts-default", voice="egopulse", input="hello")
        assert req.response_format == "wav"

    def test_default_speed_is_1(self):
        req = OpenAISpeechRequest(model="tts-default", voice="egopulse", input="hello")
        assert req.speed == 1.0


class TestNativeSpeechRequest:
    def test_valid_request(self):
        req = NativeSpeechRequest(model="tts-default", voice_id="egopulse", speech_text="hello")
        assert req.speech_text == "hello"

    def test_speech_text_required(self):
        with pytest.raises(ValidationError):
            NativeSpeechRequest(model="tts-default", voice_id="egopulse")

    def test_style_hints_optional(self):
        req = NativeSpeechRequest(
            model="tts-default", voice_id="egopulse", speech_text="hello",
            style_hints={"emotion": "gentle", "energy": 0.3}
        )
        assert req.style_hints["emotion"] == "gentle"

    def test_style_hints_defaults_none(self):
        req = NativeSpeechRequest(model="tts-default", voice_id="egopulse", speech_text="hello")
        assert req.style_hints is None


class TestErrorResponseSchema:
    def test_error_response_format(self):
        resp = ErrorResponse(
            error=ErrorDetail(
                message="not found",
                type="invalid_request_error",
                param="model",
                code="model_not_found",
            )
        )
        assert resp.error.code == "model_not_found"
        assert resp.error.message == "not found"

    def test_error_serialization(self):
        resp = ErrorResponse(
            error=ErrorDetail(message="x", type="invalid_request_error", code="test")
        )
        data = resp.model_dump()
        assert "error" in data
        assert data["error"]["code"] == "test"
