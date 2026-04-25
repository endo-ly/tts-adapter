"""Tests for ListModels and ListVoices use cases."""

import yaml

from app.application.use_cases.list_models import ListModels
from app.application.use_cases.list_voices import ListVoices
from app.infrastructure.repositories.yaml_model_profile_repository import YamlModelProfileRepository
from app.infrastructure.repositories.yaml_voice_profile_repository import YamlVoiceProfileRepository


def _write_yaml(path: str, data: dict) -> None:
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


class TestListModels:
    def test_list_models_returns_all(self, tmp_path):
        models_yaml = tmp_path / "models.yaml"
        _write_yaml(str(models_yaml), {
            "models": [
                {"id": "tts-default", "display_name": "Default", "provider": "fake", "engine": "base"},
                {"id": "irodori-base", "display_name": "Irodori Base", "provider": "irodori", "engine": "base"},
            ]
        })
        repo = YamlModelProfileRepository(yaml_path=str(models_yaml))
        uc = ListModels(model_repo=repo)
        models = uc.execute()
        assert len(models) == 2
        assert models[0].id == "tts-default"
        assert models[1].id == "irodori-base"

    def test_list_models_empty(self, tmp_path):
        models_yaml = tmp_path / "models.yaml"
        _write_yaml(str(models_yaml), {"models": []})
        repo = YamlModelProfileRepository(yaml_path=str(models_yaml))
        uc = ListModels(model_repo=repo)
        assert uc.execute() == []


class TestListVoices:
    def test_list_voices_returns_all(self, tmp_path):
        voices_dir = tmp_path / "voices"
        for name in ["egopulse", "lira"]:
            d = voices_dir / name
            d.mkdir(parents=True)
            _write_yaml(str(d / "profile.yaml"), {
                "voice_id": name,
                "display_name": name.title(),
            })

        repo = YamlVoiceProfileRepository(voices_dir=str(voices_dir))
        uc = ListVoices(voice_repo=repo)
        voices = uc.execute()
        assert len(voices) == 2
        ids = {v.voice_id for v in voices}
        assert ids == {"egopulse", "lira"}

    def test_list_voices_empty(self, tmp_path):
        voices_dir = tmp_path / "voices"
        voices_dir.mkdir()
        repo = YamlVoiceProfileRepository(voices_dir=str(voices_dir))
        uc = ListVoices(voice_repo=repo)
        assert uc.execute() == []
