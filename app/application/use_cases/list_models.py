"""List models use case."""

from app.domain.entities.model_profile import ModelProfile
from app.domain.interfaces.model_profile_repository import ModelProfileRepository


class ListModels:
    def __init__(self, model_repo: ModelProfileRepository) -> None:
        self._repo = model_repo

    def execute(self) -> list[ModelProfile]:
        return self._repo.list_all()
