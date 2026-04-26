"""Irodori CLI command builder."""


class IrodoriCliBuilder:
    @staticmethod
    def build_base_command(
        checkpoint: str,
        text: str,
        output_wav_path: str,
        model_device: str,
        codec_device: str,
        model_precision: str,
        codec_precision: str,
        num_steps: int,
        seed: int,
        speaker_kv_scale: float,
        ref_latent_path: str | None = None,
        ref_wav_path: str | None = None,
    ) -> list[str]:
        if ref_latent_path:
            ref_args = ["--ref-latent", ref_latent_path]
        elif ref_wav_path:
            ref_args = ["--ref-wav", ref_wav_path]
        else:
            raise ValueError("ref_latent_path or ref_wav_path is required")

        return [
            "uv", "run", "python", "infer.py",
            "--hf-checkpoint", checkpoint,
            "--text", text,
            *ref_args,
            "--output-wav", output_wav_path,
            "--num-steps", str(num_steps),
            "--seed", str(seed),
            "--speaker-kv-scale", str(speaker_kv_scale),
            "--model-device", model_device,
            "--codec-device", codec_device,
            "--model-precision", model_precision,
            "--codec-precision", codec_precision,
        ]

    @staticmethod
    def build_voicedesign_command(
        checkpoint: str,
        text: str,
        caption: str,
        output_wav_path: str,
        model_device: str,
        codec_device: str,
        model_precision: str,
        codec_precision: str,
        num_steps: int,
        seed: int,
    ) -> list[str]:
        return [
            "uv", "run", "python", "infer.py",
            "--hf-checkpoint", checkpoint,
            "--text", text,
            "--caption", caption,
            "--no-ref",
            "--output-wav", output_wav_path,
            "--num-steps", str(num_steps),
            "--seed", str(seed),
            "--model-device", model_device,
            "--codec-device", codec_device,
            "--model-precision", model_precision,
            "--codec-precision", codec_precision,
        ]
