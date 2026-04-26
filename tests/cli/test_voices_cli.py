"""Tests for CLI voices build-ref-latent command."""

import yaml

from app.cli.voices import _build_ref_latent


class FakeArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestBuildRefLatentCLI:
    def test_build_ref_latent_writes_profile(self, tmp_path, monkeypatch):
        assets = tmp_path / "assets"
        models_dir = assets / "models"
        voices_dir = assets / "voices" / "lira"
        models_dir.mkdir(parents=True)
        voices_dir.mkdir(parents=True)

        models_yaml = models_dir / "models.yaml"
        models_yaml.write_text(yaml.dump({
            "models": [{
                "id": "tts-default",
                "object": "model",
                "display_name": "Default TTS",
                "provider": "irodori",
                "engine": "base",
                "provider_config": {
                    "checkpoint": "Aratako/Irodori-TTS-500M-v2",
                    "model_device": "cpu",
                    "codec_device": "cpu",
                    "model_precision": "fp32",
                    "codec_precision": "fp32",
                },
            }]
        }))

        profile_yaml = voices_dir / "profile.yaml"
        profile_yaml.write_text(yaml.dump({
            "voice_id": "lira",
            "display_name": "Lira",
            "bindings": {
                "tts-default": {
                    "provider_config": {
                        "ref_wav_path": "assets/voices/lira/ref.wav",
                        "seed": 42,
                        "num_steps": 28,
                        "speaker_kv_scale": 1.0,
                    }
                }
            }
        }))

        monkeypatch.setenv("ASSETS_DIR", str(assets))
        monkeypatch.setenv("IRODORI_REPO_DIR", "/fake/irodori")
        monkeypatch.chdir(tmp_path)

        encoded_path = str(voices_dir / "ref_latent.pt")
        captured: dict[str, str] = {}

        async def fake_encode(self, **kwargs):
            import pathlib
            captured.update(kwargs)
            pathlib.Path(kwargs["output_pt_path"]).write_bytes(b"fake-pt")

        monkeypatch.setattr(
            "app.cli.voices.IrodoriLatentEncoder.encode",
            fake_encode,
        )

        args = FakeArgs(
            voice_id="lira",
            model_id="tts-default",
            write_profile=True,
        )
        _build_ref_latent(args)

        with open(profile_yaml) as f:
            updated = yaml.safe_load(f)
        binding = updated["bindings"]["tts-default"]["provider_config"]
        assert "ref_latent_path" in binding
        assert binding["ref_latent_path"] == "assets/voices/lira/ref_latent.pt"
        assert captured["ref_wav_path"] == str((voices_dir / "ref.wav").resolve())
        assert captured["output_pt_path"] == encoded_path

    def test_build_ref_latent_no_write_profile(self, tmp_path, monkeypatch):
        assets = tmp_path / "assets"
        models_dir = assets / "models"
        voices_dir = assets / "voices" / "lira"
        models_dir.mkdir(parents=True)
        voices_dir.mkdir(parents=True)

        models_yaml = models_dir / "models.yaml"
        models_yaml.write_text(yaml.dump({
            "models": [{
                "id": "tts-default",
                "object": "model",
                "display_name": "Default TTS",
                "provider": "irodori",
                "engine": "base",
                "provider_config": {
                    "checkpoint": "Aratako/Irodori-TTS-500M-v2",
                },
            }]
        }))

        profile_yaml = voices_dir / "profile.yaml"
        original_content = {
            "voice_id": "lira",
            "display_name": "Lira",
            "bindings": {
                "tts-default": {
                    "provider_config": {
                        "ref_wav_path": "assets/voices/lira/ref.wav",
                        "seed": 42,
                    }
                }
            }
        }
        profile_yaml.write_text(yaml.dump(original_content))

        monkeypatch.setenv("ASSETS_DIR", str(assets))
        monkeypatch.setenv("IRODORI_REPO_DIR", "/fake/irodori")
        monkeypatch.chdir(tmp_path)

        async def fake_encode(self, **kwargs):
            import pathlib
            pathlib.Path(kwargs["output_pt_path"]).write_bytes(b"fake-pt")

        monkeypatch.setattr(
            "app.cli.voices.IrodoriLatentEncoder.encode",
            fake_encode,
        )

        args = FakeArgs(
            voice_id="lira",
            model_id="tts-default",
            write_profile=False,
        )
        _build_ref_latent(args)

        with open(profile_yaml) as f:
            updated = yaml.safe_load(f)
        binding = updated["bindings"]["tts-default"]["provider_config"]
        assert "ref_latent_path" not in binding

    def test_build_ref_latent_keeps_configured_profile_path(self, tmp_path, monkeypatch):
        assets = tmp_path / "assets"
        models_dir = assets / "models"
        voices_dir = assets / "voices" / "lira"
        models_dir.mkdir(parents=True)
        voices_dir.mkdir(parents=True)

        models_yaml = models_dir / "models.yaml"
        models_yaml.write_text(yaml.dump({
            "models": [{
                "id": "tts-default",
                "object": "model",
                "display_name": "Default TTS",
                "provider": "irodori",
                "engine": "base",
                "provider_config": {
                    "checkpoint": "Aratako/Irodori-TTS-500M-v2",
                },
            }]
        }))

        profile_yaml = voices_dir / "profile.yaml"
        profile_yaml.write_text(yaml.dump({
            "voice_id": "lira",
            "display_name": "Lira",
            "bindings": {
                "tts-default": {
                    "provider_config": {
                        "ref_wav_path": "assets/voices/lira/ref.wav",
                        "ref_latent_path": "assets/voices/lira/custom.pt",
                    }
                }
            }
        }))

        monkeypatch.setenv("ASSETS_DIR", str(assets))
        monkeypatch.setenv("IRODORI_REPO_DIR", "/fake/irodori")
        monkeypatch.chdir(tmp_path)
        captured: dict[str, str] = {}

        async def fake_encode(self, **kwargs):
            import pathlib
            captured.update(kwargs)
            pathlib.Path(kwargs["output_pt_path"]).write_bytes(b"fake-pt")

        monkeypatch.setattr(
            "app.cli.voices.IrodoriLatentEncoder.encode",
            fake_encode,
        )

        args = FakeArgs(
            voice_id="lira",
            model_id="tts-default",
            write_profile=True,
        )
        _build_ref_latent(args)

        with open(profile_yaml) as f:
            updated = yaml.safe_load(f)
        binding = updated["bindings"]["tts-default"]["provider_config"]
        assert binding["ref_latent_path"] == "assets/voices/lira/custom.pt"
        assert captured["output_pt_path"] == str((tmp_path / "assets/voices/lira/custom.pt").resolve())
