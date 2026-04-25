"""API schemas for OpenAI-compatible speech endpoint."""

from pydantic import BaseModel, Field


class OpenAISpeechRequest(BaseModel):
    model: str
    voice: str
    input: str = Field(min_length=1)
    response_format: str = "wav"
    speed: float = 1.0
