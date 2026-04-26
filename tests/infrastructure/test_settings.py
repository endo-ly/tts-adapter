"""Tests for Settings."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.infrastructure.config.settings import Settings


@pytest.fixture(autouse=True)
def _clear_settings_env(monkeypatch):
    for key in ("PROJECT_ROOT", "ASSETS_DIR", "TMP_DIR", "IRODORI_REPO_DIR", "HOST", "PORT"):
        monkeypatch.delenv(key, raising=False)


class TestSettingsDefaults:
    def test_default_host(self):
        s = Settings()
        assert s.host == "127.0.0.1"

    def test_default_port(self):
        s = Settings()
        assert s.port == 8012

    def test_default_assets_dir(self):
        s = Settings()
        assert Path(s.assets_dir).is_absolute()
        assert s.assets_dir.endswith("assets")

    def test_default_tmp_dir(self):
        s = Settings()
        assert Path(s.tmp_dir).is_absolute()
        assert s.tmp_dir.endswith("tmp")

    def test_default_timeout_sec(self):
        s = Settings()
        assert s.timeout_sec == 120

    def test_default_max_concurrency(self):
        s = Settings()
        assert s.max_concurrency == 1


class TestSettingsFromEnv:
    def test_irodori_repo_dir_from_env(self):
        with patch.dict(os.environ, {"IRODORI_REPO_DIR": "/opt/irodori"}):
            s = Settings()
            assert s.irodori_repo_dir == "/opt/irodori"

    def test_irodori_repo_dir_default_is_none(self):
        with patch.dict(os.environ, {}, clear=False):
            env = os.environ.copy()
            env.pop("IRODORI_REPO_DIR", None)
            with patch.dict(os.environ, env, clear=True):
                s = Settings()
                assert s.irodori_repo_dir is None

    def test_custom_port_from_env(self):
        with patch.dict(os.environ, {"PORT": "9000"}):
            s = Settings()
            assert s.port == 9000

    def test_custom_host_from_env(self):
        with patch.dict(os.environ, {"HOST": "0.0.0.0"}):
            s = Settings()
            assert s.host == "0.0.0.0"

    def test_irodori_repo_dir_from_dotenv(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("IRODORI_REPO_DIR", raising=False)
        (tmp_path / ".env").write_text(
            "IRODORI_REPO_DIR='C:\\svc\\runtimes\\Irodori-TTS'\n",
            encoding="utf-8",
        )

        s = Settings()

        assert s.irodori_repo_dir == "C:\\svc\\runtimes\\Irodori-TTS"

    def test_quoted_windows_path_with_control_character_is_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("IRODORI_REPO_DIR", raising=False)
        (tmp_path / ".env").write_text(
            'IRODORI_REPO_DIR="C:\\svc\\runtimes\\Irodori-TTS"\n',
            encoding="utf-8",
        )

        with pytest.raises(ValidationError, match="control characters"):
            Settings()
