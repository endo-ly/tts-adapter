"""Temp file manager for WAV output."""

import os
import uuid
from pathlib import Path


class TempFileManager:
    def __init__(self, tmp_dir: str) -> None:
        self._tmp_dir = Path(tmp_dir)
        self._tmp_dir.mkdir(parents=True, exist_ok=True)

    def create_temp_wav_path(self) -> str:
        filename = f"{uuid.uuid4()}.wav"
        return str(self._tmp_dir / filename)

    def cleanup(self, path: str) -> None:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
