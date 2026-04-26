"""Irodori TTS provider — CLI subprocess implementation."""

import asyncio
import os

from app.domain.errors import ProviderExecutionError
from app.domain.value_objects.synthesis_request import ProviderSynthesisRequest
from app.domain.value_objects.synthesis_result import SynthesisResult
from app.infrastructure.providers.irodori.cli_builder import IrodoriCliBuilder
from app.infrastructure.providers.irodori.subprocess_runner import SubprocessRunner
from app.infrastructure.tempfiles.manager import TempFileManager


class IrodoriProvider:
    provider_name: str = "irodori"

    def __init__(self, irodori_repo_dir: str, tmp_dir: str, timeout_sec: int = 120) -> None:
        self._irodori_repo_dir = irodori_repo_dir
        self._tmp_manager = TempFileManager(tmp_dir=tmp_dir)
        self._timeout_sec = timeout_sec
        self._semaphore = asyncio.Semaphore(1)
        self._runner: SubprocessRunner = SubprocessRunner(timeout_sec=timeout_sec)

    async def synthesize(self, request: ProviderSynthesisRequest) -> SynthesisResult:
        async with self._semaphore:
            return await self._do_synthesize(request)

    async def _do_synthesize(self, request: ProviderSynthesisRequest) -> SynthesisResult:
        cfg = request.provider_config
        output_path = self._tmp_manager.create_temp_wav_path()

        try:
            if request.engine == "voicedesign":
                cmd = IrodoriCliBuilder.build_voicedesign_command(
                    checkpoint=cfg["checkpoint"],
                    text=request.text,
                    caption=cfg["caption"],
                    output_wav_path=output_path,
                    model_device=cfg.get("model_device", "cpu"),
                    codec_device=cfg.get("codec_device", "cpu"),
                    model_precision=cfg.get("model_precision", "fp32"),
                    codec_precision=cfg.get("codec_precision", "fp32"),
                    num_steps=cfg.get("num_steps", 28),
                    seed=cfg.get("seed", 0),
                )
            else:
                cmd = IrodoriCliBuilder.build_base_command(
                    checkpoint=cfg["checkpoint"],
                    text=request.text,
                    ref_latent_path=cfg["ref_latent_path"],
                    output_wav_path=output_path,
                    model_device=cfg.get("model_device", "cpu"),
                    codec_device=cfg.get("codec_device", "cpu"),
                    model_precision=cfg.get("model_precision", "fp32"),
                    codec_precision=cfg.get("codec_precision", "fp32"),
                    num_steps=cfg.get("num_steps", 28),
                    seed=cfg.get("seed", 0),
                    speaker_kv_scale=cfg.get("speaker_kv_scale", 1.0),
                )

            await self._runner.run(cmd, cwd=self._irodori_repo_dir)

            if not os.path.exists(output_path):
                raise ProviderExecutionError(
                    "irodori", "Output WAV file was not created"
                )

            if os.path.getsize(output_path) == 0:
                raise ProviderExecutionError(
                    "irodori", "Output WAV file is empty"
                )

            with open(output_path, "rb") as f:
                audio_bytes = f.read()

            return SynthesisResult(audio_bytes=audio_bytes)

        finally:
            self._tmp_manager.cleanup(output_path)
