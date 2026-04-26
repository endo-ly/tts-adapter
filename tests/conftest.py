"""Global test fixtures — ensure asset config files exist before tests."""

import shutil
from pathlib import Path

import pytest


@pytest.fixture(autouse=True, scope="session")
def _setup_asset_configs():
    base = Path(__file__).resolve().parent.parent / "assets"
    copies: list[tuple[Path, Path]] = [
        (base / "models" / "models.example.yaml", base / "models" / "models.yaml"),
        (
            base / "voices" / "your-voice-name" / "profile.example.yaml",
            base / "voices" / "your-voice-name" / "profile.yaml",
        ),
    ]
    created: list[Path] = []
    for src, dst in copies:
        if not dst.exists() and src.exists():
            shutil.copy2(src, dst)
            created.append(dst)
    yield
    for p in created:
        p.unlink(missing_ok=True)
