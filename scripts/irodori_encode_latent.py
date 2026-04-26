"""Bridge script: encode a WAV file into a DACVAE latent tensor (.pt).

Runs inside Irodori-TTS's environment (cwd = IRODORI_REPO_DIR).
Called by tts-adapter's LatentEncoder via subprocess.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import torch
import torchaudio
from irodori_tts.codec import DACVAECodec


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-wav", required=True)
    parser.add_argument("--output-pt", required=True)
    parser.add_argument("--checkpoint")
    parser.add_argument("--codec-repo", default="Aratako/Semantic-DACVAE-Japanese-32dim")
    parser.add_argument("--model-device", default="cpu")
    parser.add_argument("--codec-device", default="cpu")
    parser.add_argument("--model-precision", default="fp32")
    parser.add_argument("--codec-precision", default="fp32")
    args = parser.parse_args()

    dtype = torch.bfloat16 if args.codec_precision == "bf16" else torch.float32

    codec = DACVAECodec.load(
        repo_id=args.codec_repo,
        device=args.codec_device,
        dtype=dtype,
        deterministic_encode=True,
    )

    wav, sr = torchaudio.load(args.input_wav)
    if wav.shape[0] != 1:
        wav = wav.mean(dim=0, keepdim=True)
    wav = wav.unsqueeze(0).to(device=args.codec_device, dtype=dtype)

    latent = codec.encode_waveform(wav, sample_rate=int(sr))[0].cpu()
    torch.save(latent, args.output_pt)
    print(f"Saved latent {latent.shape} -> {args.output_pt}")


if __name__ == "__main__":
    main()
