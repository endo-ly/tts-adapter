"""Tests for SynthesizeSpeech use case."""

import pytest

from app.application.services.option_merger import OptionMerger
from app.application.services.profile_resolver import ProfileResolver
from app.application.services.provider_registry import ProviderRegistry
from app.application.use_cases.synthesize_speech import SynthesizeSpeech
from app.domain.errors import UnsupportedResponseFormatError, UnsupportedSpeedError
from app.infrastructure.providers.fake.provider import FakeProvider
from app.infrastructure.repositories.yaml_model_profile_repository import YamlModelProfileRepository
from app.infrastructure.repositories.yaml_voice_profile_repository import YamlVoiceProfileRepository
import yaml


def _write_yaml(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)


def _setup_fixtures(tmp_path):
    models_yaml = tmp_path / "models.yaml"
    _write_yaml(str(models_yaml), {
        "models": [{
            "id": "tts-default",
            "display_name": "Default",
            "provider": "fake",
            "engine": "base",
            "defaults": {"response_format": "wav", "speed": 1.0, "timeout_sec": 120},
            "provider_config": {},
        }]
    })

    voices_dir = tmp_path / "voices"
    ego_dir = voices_dir / "egopulse"
    ego_dir.mkdir(parents=True)
    _write_yaml(str(ego_dir / "profile.yaml"), {
        "voice_id": "egopulse",
        "display_name": "EgoPulse",
        "defaults": {"preferred_model": "tts-default"},
        "bindings": {"tts-default": {"provider_config": {}}},
    })

    model_repo = YamlModelProfileRepository(yaml_path=str(models_yaml))
    voice_repo = YamlVoiceProfileRepository(voices_dir=str(voices_dir))
    resolver = ProfileResolver(model_repo=model_repo, voice_repo=voice_repo)

    registry = ProviderRegistry()
    registry.register(FakeProvider())

    return SynthesizeSpeech(
        profile_resolver=resolver,
        provider_registry=registry,
        option_merger=OptionMerger(),
    )


class TestSynthesizeSpeech:
    async def test_synthesize_with_fake_provider_returns_wav(self, tmp_path):
        uc = _setup_fixtures(tmp_path)
        result = await uc.execute(
            model_id="tts-default",
            voice_id="egopulse",
            text="こんにちは",
        )
        assert result.audio_bytes.startswith(b"RIFF")
        assert result.media_type == "audio/wav"

    async def test_synthesize_validates_response_format(self, tmp_path):
        uc = _setup_fixtures(tmp_path)
        with pytest.raises(UnsupportedResponseFormatError):
            await uc.execute(
                model_id="tts-default",
                voice_id="egopulse",
                text="test",
                response_format="mp3",
            )

    async def test_synthesize_validates_speed(self, tmp_path):
        uc = _setup_fixtures(tmp_path)
        with pytest.raises(UnsupportedSpeedError):
            await uc.execute(
                model_id="tts-default",
                voice_id="egopulse",
                text="test",
                speed=2.0,
            )
