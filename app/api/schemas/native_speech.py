"""API schemas for Native speech endpoint."""

from typing import Any

from pydantic import BaseModel, Field


class NativeSpeechRequest(BaseModel):
    model: str
    voice_id: str
    speech_text: str = Field(min_length=1)
    style_hints: dict[str, Any] | None = None
    response_format: str = "wav"
