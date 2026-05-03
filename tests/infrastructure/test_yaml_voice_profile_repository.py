"""Tests for YAML VoiceProfileRepository."""

import pytest
import yaml

from app.domain.errors import InvalidProfileError, VoiceNotFoundError
from app.domain.entities.voice_profile import VoiceProfile
from app.infrastructure.repositories.yaml_voice_profile_repository import (
    YamlVoiceProfileRepository,
)


def _write_yaml(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)


class TestYamlVoiceProfileRepository:
    def test_list_all_scans_subdirs(self, tmp_path):
        voices_dir = tmp_path / "voices"
        egopulse_dir = voices_dir / "egopulse"
        egopulse_dir.mkdir(parents=True)
        _write_yaml(str(egopulse_dir / "profile.yaml"), {
            "voice_id": "egopulse",
            "display_name": "EgoPulse",
            "description": "静かで知的",
            "bindings": {"tts-default": {"provider_config": {"seed": 42}}},
        })

        lira_dir = voices_dir / "lira"
        lira_dir.mkdir()
        _write_yaml(str(lira_dir / "profile.yaml"), {
            "voice_id": "lira",
            "display_name": "Lira",
        })

        repo = YamlVoiceProfileRepository(voices_dir=str(voices_dir))
        voices = repo.list_all()
        assert len(voices) == 2
        ids = {v.voice_id for v in voices}
        assert ids == {"egopulse", "lira"}

    def test_get_by_id_found(self, tmp_path):
        voices_dir = tmp_path / "voices"
        egopulse_dir = voices_dir / "egopulse"
        egopulse_dir.mkdir(parents=True)
        _write_yaml(str(egopulse_dir / "profile.yaml"), {
            "voice_id": "egopulse",
            "display_name": "EgoPulse",
        })

        repo = YamlVoiceProfileRepository(voices_dir=str(voices_dir))
        voice = repo.get_by_id("egopulse")
        assert voice.voice_id == "egopulse"
        assert voice.display_name == "EgoPulse"

    def test_get_by_id_not_found_raises(self, tmp_path):
        voices_dir = tmp_path / "voices"
        voices_dir.mkdir()

        repo = YamlVoiceProfileRepository(voices_dir=str(voices_dir))
        with pytest.raises(VoiceNotFoundError) as exc_info:
            repo.get_by_id("nonexistent")
        assert exc_info.value.voice_id == "nonexistent"

    def test_invalid_profile_raises(self, tmp_path):
        voices_dir = tmp_path / "voices"
        bad_dir = voices_dir / "bad"
        bad_dir.mkdir(parents=True)
        (bad_dir / "profile.yaml").write_text("voice_id:", encoding="utf-8")  # missing required

        repo = YamlVoiceProfileRepository(voices_dir=str(voices_dir))
        with pytest.raises(InvalidProfileError):
            repo.list_all()

    def test_empty_voices_dir_returns_empty_list(self, tmp_path):
        voices_dir = tmp_path / "voices"
        voices_dir.mkdir()

        repo = YamlVoiceProfileRepository(voices_dir=str(voices_dir))
        assert repo.list_all() == []

    def test_subdir_without_profile_yaml_is_skipped(self, tmp_path):
        voices_dir = tmp_path / "voices"
        empty_dir = voices_dir / "noyaml"
        empty_dir.mkdir(parents=True)

        repo = YamlVoiceProfileRepository(voices_dir=str(voices_dir))
        assert repo.list_all() == []

    def test_duplicate_voice_id_raises(self, tmp_path):
        voices_dir = tmp_path / "voices"
        voice1_dir = voices_dir / "voice-a"
        voice1_dir.mkdir(parents=True)
        _write_yaml(str(voice1_dir / "profile.yaml"), {
            "voice_id": "same-voice",
            "display_name": "Voice A",
        })
        voice2_dir = voices_dir / "voice-b"
        voice2_dir.mkdir()
        _write_yaml(str(voice2_dir / "profile.yaml"), {
            "voice_id": "same-voice",
            "display_name": "Voice B",
        })
        repo = YamlVoiceProfileRepository(voices_dir=str(voices_dir))
        with pytest.raises(InvalidProfileError, match="Duplicate voice id"):
            repo.list_all()
