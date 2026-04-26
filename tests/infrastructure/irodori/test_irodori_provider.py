"""Tests for IrodoriProvider."""

import os
from pathlib import Path

import pytest

from app.domain.errors import ProviderExecutionError
from app.domain.value_objects.synthesis_request import ProviderSynthesisRequest
from app.infrastructure.providers.irodori.provider import IrodoriProvider


def _make_request(**overrides) -> ProviderSynthesisRequest:
    defaults: dict = {
        "model_id": "tts-default",
        "voice_id": "egopulse",
        "text": "こんにちは",
        "provider": "irodori",
        "engine": "base",
        "provider_config": {
            "checkpoint": "Aratako/Irodori-TTS-500M-v2",
            "ref_latent_path": "assets/voices/egopulse/ref_latent.pt",
            "seed": 42,
            "num_steps": 28,
            "speaker_kv_scale": 1.1,
            "model_device": "cpu",
            "codec_device": "cpu",
            "model_precision": "fp32",
            "codec_precision": "fp32",
        },
    }
    defaults.update(overrides)
    return ProviderSynthesisRequest(**defaults)


class FakeSubprocessRunner:
    """Test double for SubprocessRunner that creates wav files."""

    def __init__(self, wav_bytes: bytes | None = None) -> None:
        self._wav_bytes = wav_bytes
        self.cmd: list[str] | None = None
        self.cwd: str | None = None

    async def run(self, cmd: list[str], cwd: str | None = None) -> str:
        self.cmd = cmd
        self.cwd = cwd
        if self._wav_bytes is None:
            return ""
        for i, part in enumerate(cmd):
            if part == "--output-wav" and i + 1 < len(cmd):
                with open(cmd[i + 1], "wb") as f:
                    f.write(self._wav_bytes)
        return ""


WAV_HEADER = (
    b"RIFF\x24\x00\x00\x00WAVEfmt "
    b"\x10\x00\x00\x00\x01\x00\x01\x00"
    b"D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00"
    b"data\x00\x00\x00\x00"
)


class TestIrodoriProvider:
    def test_provider_name(self, tmp_path):
        p = IrodoriProvider(
            irodori_repo_dir="/opt/irodori",
            tmp_dir=str(tmp_path),
            base_dir=str(tmp_path),
        )
        assert p.provider_name == "irodori"

    async def test_synthesize_with_mock_subprocess(self, tmp_path):
        provider = IrodoriProvider(
            irodori_repo_dir="/opt/irodori",
            tmp_dir=str(tmp_path),
            base_dir=str(tmp_path),
        )
        provider._runner = FakeSubprocessRunner(wav_bytes=WAV_HEADER)

        result = await provider.synthesize(_make_request())
        assert result.audio_bytes.startswith(b"RIFF")
        assert result.media_type == "audio/wav"

    async def test_synthesize_resolves_relative_paths_for_irodori_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        provider = IrodoriProvider(
            irodori_repo_dir="/opt/irodori",
            tmp_dir="tmp",
            base_dir=str(tmp_path),
        )
        runner = FakeSubprocessRunner(wav_bytes=WAV_HEADER)
        provider._runner = runner

        await provider.synthesize(_make_request())

        assert runner.cmd is not None
        assert runner.cwd == "/opt/irodori"
        cmd = runner.cmd
        assert cmd[cmd.index("--ref-latent") + 1] == str(
            (tmp_path / "assets/voices/egopulse/ref_latent.pt").resolve()
        )
        assert Path(cmd[cmd.index("--output-wav") + 1]).is_absolute()

    async def test_tmp_wav_deleted_after_synthesize(self, tmp_path):
        created_files: list[str] = []

        class TrackingRunner(FakeSubprocessRunner):
            async def run(self, cmd, cwd=None):  # type: ignore[override]
                for i, part in enumerate(cmd):
                    if part == "--output-wav" and i + 1 < len(cmd):
                        created_files.append(cmd[i + 1])
                return await super().run(cmd)

        provider = IrodoriProvider(
            irodori_repo_dir="/opt/irodori",
            tmp_dir=str(tmp_path),
            base_dir=str(tmp_path),
        )
        provider._runner = TrackingRunner(wav_bytes=WAV_HEADER)
        await provider.synthesize(_make_request())

        for f in created_files:
            assert not os.path.exists(f), f"tmp wav should be deleted: {f}"

    async def test_synthesize_missing_output_raises(self, tmp_path):
        provider = IrodoriProvider(
            irodori_repo_dir="/opt/irodori",
            tmp_dir=str(tmp_path),
            base_dir=str(tmp_path),
        )
        provider._runner = FakeSubprocessRunner(wav_bytes=None)

        with pytest.raises(ProviderExecutionError):
            await provider.synthesize(_make_request())

    async def test_synthesize_empty_output_raises(self, tmp_path):
        provider = IrodoriProvider(
            irodori_repo_dir="/opt/irodori",
            tmp_dir=str(tmp_path),
            base_dir=str(tmp_path),
        )
        provider._runner = FakeSubprocessRunner(wav_bytes=b"")

        with pytest.raises(ProviderExecutionError):
            await provider.synthesize(_make_request())

    def test_concurrency_limit_is_1(self, tmp_path):
        provider = IrodoriProvider(
            irodori_repo_dir="/opt/irodori",
            tmp_dir=str(tmp_path),
            base_dir=str(tmp_path),
        )
        assert provider._semaphore._value == 1
