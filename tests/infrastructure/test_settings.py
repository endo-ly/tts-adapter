"""Tests for Settings."""

import os
from unittest.mock import patch

from app.infrastructure.config.settings import Settings


class TestSettingsDefaults:
    def test_default_host(self):
        s = Settings()
        assert s.host == "127.0.0.1"

    def test_default_port(self):
        s = Settings()
        assert s.port == 8012

    def test_default_assets_dir(self):
        s = Settings()
        assert s.assets_dir == "./assets"

    def test_default_tmp_dir(self):
        s = Settings()
        assert s.tmp_dir == "./tmp"

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
