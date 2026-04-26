"""YAML-backed ModelProfileRepository."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from app.domain.entities.model_profile import ModelProfile
from app.domain.errors import InvalidProfileError, ModelNotFoundError
from app.domain.interfaces.model_profile_repository import ModelProfileRepository


class YamlModelProfileRepository:
    def __init__(self, yaml_path: str) -> None:
        self._yaml_path = Path(yaml_path)
        self._cache: list[ModelProfile] | None = None

    def _load(self) -> list[ModelProfile]:
        if self._cache is not None:
            return self._cache

        try:
            with open(self._yaml_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise InvalidProfileError(f"Invalid YAML syntax: {e}") from e

        if not isinstance(raw, dict) or "models" not in raw:
            raise InvalidProfileError("YAML must contain a 'models' key")

        models_data = raw["models"]
        if not isinstance(models_data, list):
            raise InvalidProfileError("'models' must be a list")

        try:
            models = [ModelProfile.model_validate(m) for m in models_data]
        except ValidationError as e:
            raise InvalidProfileError(f"Invalid model profile: {e}") from e

        ids = [m.id for m in models]
        duplicate_ids = sorted({model_id for model_id in ids if ids.count(model_id) > 1})
        if duplicate_ids:
            raise InvalidProfileError(
                f"Duplicate model id(s): {', '.join(duplicate_ids)}"
            )

        self._cache = models
        return self._cache

    def list_all(self) -> list[ModelProfile]:
        return list(self._load())

    def get_by_id(self, model_id: str) -> ModelProfile:
        for model in self._load():
            if model.id == model_id:
                return model
        raise ModelNotFoundError(model_id)
