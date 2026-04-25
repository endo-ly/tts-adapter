"""SynthesisResult value object."""

from typing import Literal

from pydantic import BaseModel


class SynthesisResult(BaseModel):
    audio_bytes: bytes
    media_type: Literal["audio/wav"] = "audio/wav"
    format: Literal["wav"] = "wav"
