"""ModelProfileRepository interface."""

from typing import Protocol, runtime_checkable

from app.domain.entities.model_profile import ModelProfile


@runtime_checkable
class ModelProfileRepository(Protocol):
    async def get_by_id(self, model_id: str) -> ModelProfile: ...
    async def list_all(self) -> list[ModelProfile]: ...
