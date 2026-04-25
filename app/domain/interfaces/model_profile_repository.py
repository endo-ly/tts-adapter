"""ModelProfileRepository interface."""

from typing import Protocol, runtime_checkable

from app.domain.entities.model_profile import ModelProfile


@runtime_checkable
class ModelProfileRepository(Protocol):
    def get_by_id(self, model_id: str) -> ModelProfile: ...
    def list_all(self) -> list[ModelProfile]: ...
