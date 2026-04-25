"""ModelProfile entity."""

from typing import Any

from pydantic import BaseModel, Field


class ModelDefaults(BaseModel):
    response_format: str = "wav"
    speed: float = 1.0
    timeout_sec: int = 120


class ModelProfile(BaseModel):
    id: str
    object: str = "model"
    display_name: str
    provider: str
    engine: str
    defaults: ModelDefaults = Field(default_factory=ModelDefaults)
    provider_config: dict[str, Any] = Field(default_factory=dict)
