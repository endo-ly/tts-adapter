"""Tests for Irodori CLI Builder."""

from app.infrastructure.providers.irodori.cli_builder import IrodoriCliBuilder


class TestIrodoriCliBuilder:
    def test_build_base_command_returns_list_str(self):
        cmd = IrodoriCliBuilder.build_base_command(
            irodori_repo_dir="/opt/irodori",
            checkpoint="Aratako/Irodori-TTS-500M-v2",
            text="こんにちは",
            ref_latent_path="assets/voices/egopulse/ref_latent.pt",
            output_wav_path="tmp/out.wav",
            model_device="cuda",
            codec_device="cuda",
            model_precision="bf16",
            codec_precision="bf16",
            num_steps=28,
            seed=42,
            speaker_kv_scale=1.1,
        )
        assert isinstance(cmd, list)
        for part in cmd:
            assert isinstance(part, str)
        assert "shell" not in str(cmd).lower()

    def test_build_base_command_includes_all_flags(self):
        cmd = IrodoriCliBuilder.build_base_command(
            irodori_repo_dir="/opt/irodori",
            checkpoint="Aratako/Irodori-TTS-500M-v2",
            text="こんにちは",
            ref_latent_path="assets/voices/egopulse/ref_latent.pt",
            output_wav_path="tmp/out.wav",
            model_device="cuda",
            codec_device="cuda",
            model_precision="bf16",
            codec_precision="bf16",
            num_steps=28,
            seed=42,
            speaker_kv_scale=1.1,
        )
        cmd_str = " ".join(cmd)
        assert "--hf-checkpoint" in cmd_str
        assert "Aratako/Irodori-TTS-500M-v2" in cmd_str
        assert "--text" in cmd_str
        assert "こんにちは" in cmd_str
        assert "--ref-latent" in cmd_str
        assert "--output-wav" in cmd_str
        assert "--num-steps" in cmd_str
        assert "--seed" in cmd_str
        assert "--speaker-kv-scale" in cmd_str
        assert "--model-device" in cmd_str
        assert "--codec-device" in cmd_str
        assert "--model-precision" in cmd_str
        assert "--codec-precision" in cmd_str

    def test_build_base_command_starts_with_uv_run(self):
        cmd = IrodoriCliBuilder.build_base_command(
            irodori_repo_dir="/opt/irodori",
            checkpoint="x",
            text="test",
            ref_latent_path="ref.pt",
            output_wav_path="out.wav",
            model_device="cpu",
            codec_device="cpu",
            model_precision="fp32",
            codec_precision="fp32",
            num_steps=10,
            seed=1,
            speaker_kv_scale=1.0,
        )
        assert cmd[0] == "uv"
        assert cmd[1] == "run"

    def test_build_voicedesign_command_includes_caption_and_no_ref(self):
        cmd = IrodoriCliBuilder.build_voicedesign_command(
            irodori_repo_dir="/opt/irodori",
            checkpoint="Aratako/Irodori-TTS-500M-v2-VoiceDesign",
            text="こんにちは",
            caption="20代前半の男性",
            output_wav_path="tmp/out.wav",
            model_device="cuda",
            codec_device="cuda",
            model_precision="bf16",
            codec_precision="bf16",
            num_steps=28,
            seed=42,
        )
        cmd_str = " ".join(cmd)
        assert "--caption" in cmd_str
        assert "20代前半の男性" in cmd_str
        assert "--no-ref" in cmd_str
        # voicedesign should NOT have --ref-latent or --speaker-kv-scale
        assert "--ref-latent" not in cmd_str
        assert "--speaker-kv-scale" not in cmd_str

    def test_build_base_command_no_shell_injection_vector(self):
        """Ensure command is list[str], not a single shell string."""
        cmd = IrodoriCliBuilder.build_base_command(
            irodori_repo_dir="/opt/irodori",
            checkpoint="x",
            text="test; rm -rf /",
            ref_latent_path="ref.pt",
            output_wav_path="out.wav",
            model_device="cpu",
            codec_device="cpu",
            model_precision="fp32",
            codec_precision="fp32",
            num_steps=10,
            seed=1,
            speaker_kv_scale=1.0,
        )
        # The text "test; rm -rf /" should be a single element, not split
        assert any("test; rm -rf /" in part for part in cmd)
