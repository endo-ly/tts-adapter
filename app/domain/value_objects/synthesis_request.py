"""ProviderSynthesisRequest value object."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProviderSynthesisRequest(BaseModel):
    model_id: str
    voice_id: str
    text: str = Field(min_length=1)
    response_format: Literal["wav"] = "wav"
    speed: float = 1.0
    provider: str
    engine: str
    provider_config: dict[str, Any]
