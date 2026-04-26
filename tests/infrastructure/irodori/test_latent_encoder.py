"""Tests for Irodori latent encoder command construction."""

from app.infrastructure.providers.irodori.latent_encoder import IrodoriLatentEncoder


class CapturingRunner:
    def __init__(self) -> None:
        self.cmd: list[str] | None = None
        self.cwd: str | None = None

    async def run(self, cmd: list[str], cwd: str | None = None) -> str:
        self.cmd = cmd
        self.cwd = cwd
        return ""


async def test_encode_passes_bridge_arguments() -> None:
    encoder = IrodoriLatentEncoder(irodori_repo_dir="/opt/irodori")
    runner = CapturingRunner()
    encoder._runner = runner  # type: ignore[assignment]

    await encoder.encode(
        ref_wav_path="/repo/assets/voices/lira/ref.wav",
        output_pt_path="/repo/assets/voices/lira/ref_latent.pt",
        checkpoint="Aratako/Irodori-TTS-500M-v2",
        codec_repo="Aratako/Semantic-DACVAE-Japanese-32dim",
        model_device="cuda",
        codec_device="cuda",
        model_precision="bf16",
        codec_precision="bf16",
    )

    assert runner.cwd == "/opt/irodori"
    assert runner.cmd is not None
    cmd_str = " ".join(runner.cmd)
    assert "--checkpoint Aratako/Irodori-TTS-500M-v2" in cmd_str
    assert "--model-device cuda" in cmd_str
    assert "--model-precision bf16" in cmd_str
    assert "--codec-device cuda" in cmd_str
    assert "--codec-precision bf16" in cmd_str
