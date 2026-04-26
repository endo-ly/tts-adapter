"""Tests for YAML ModelProfileRepository."""

import os
import tempfile

import pytest
import yaml

from app.domain.errors import InvalidProfileError, ModelNotFoundError
from app.domain.entities.model_profile import ModelProfile
from app.infrastructure.repositories.yaml_model_profile_repository import (
    YamlModelProfileRepository,
)


def _write_yaml(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)


class TestYamlModelProfileRepository:
    def test_list_all_returns_models(self, tmp_path):
        yaml_path = tmp_path / "models.yaml"
        _write_yaml(str(yaml_path), {
            "models": [
                {
                    "id": "tts-default",
                    "object": "model",
                    "display_name": "Default TTS",
                    "provider": "irodori",
                    "engine": "base",
                    "defaults": {"response_format": "wav", "speed": 1.0, "timeout_sec": 120},
                    "provider_config": {"checkpoint": "Aratako/Irodori-TTS-500M-v2"},
                },
                {
                    "id": "fake-model",
                    "object": "model",
                    "display_name": "Fake Model",
                    "provider": "fake",
                    "engine": "base",
                },
            ]
        })
        repo = YamlModelProfileRepository(yaml_path=str(yaml_path))
        models = repo.list_all()
        assert len(models) == 2
        assert all(isinstance(m, ModelProfile) for m in models)

    def test_get_by_id_found(self, tmp_path):
        yaml_path = tmp_path / "models.yaml"
        _write_yaml(str(yaml_path), {
            "models": [
                {
                    "id": "tts-default",
                    "object": "model",
                    "display_name": "Default TTS",
                    "provider": "irodori",
                    "engine": "base",
                },
            ]
        })
        repo = YamlModelProfileRepository(yaml_path=str(yaml_path))
        model = repo.get_by_id("tts-default")
        assert model.id == "tts-default"

    def test_get_by_id_not_found_raises(self, tmp_path):
        yaml_path = tmp_path / "models.yaml"
        _write_yaml(str(yaml_path), {"models": []})
        repo = YamlModelProfileRepository(yaml_path=str(yaml_path))
        with pytest.raises(ModelNotFoundError) as exc_info:
            repo.get_by_id("nonexistent")
        assert exc_info.value.model_id == "nonexistent"

    def test_invalid_yaml_raises_invalid_profile_error(self, tmp_path):
        yaml_path = tmp_path / "models.yaml"
        yaml_path.write_text("models: [{id: }]", encoding="utf-8")  # missing required fields
        repo = YamlModelProfileRepository(yaml_path=str(yaml_path))
        with pytest.raises(InvalidProfileError):
            repo.list_all()

    def test_malformed_yaml_syntax_raises(self, tmp_path):
        yaml_path = tmp_path / "models.yaml"
        yaml_path.write_text("models: [\n{invalid yaml", encoding="utf-8")
        repo = YamlModelProfileRepository(yaml_path=str(yaml_path))
        with pytest.raises(InvalidProfileError):
            repo.list_all()

    def test_list_all_caches_result(self, tmp_path):
        yaml_path = tmp_path / "models.yaml"
        _write_yaml(str(yaml_path), {
            "models": [
                {
                    "id": "tts-default",
                    "display_name": "Default",
                    "provider": "fake",
                    "engine": "base",
                },
            ]
        })
        repo = YamlModelProfileRepository(yaml_path=str(yaml_path))
        first = repo.list_all()
        second = repo.list_all()
        cached = repo._cache
        assert cached is not None
        repo.list_all()
        assert repo._cache is cached
