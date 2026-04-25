"""Tests for TempFileManager."""

import os

from app.infrastructure.tempfiles.manager import TempFileManager


class TestTempFileManager:
    def test_create_temp_wav_path_contains_uuid_and_wav(self, tmp_path):
        mgr = TempFileManager(tmp_dir=str(tmp_path))
        path = mgr.create_temp_wav_path()
        basename = os.path.basename(path)
        assert basename.endswith(".wav")
        # uuid part: 36 chars + ".wav" = 40 chars
        assert len(basename) > 4

    def test_create_temp_wav_paths_are_unique(self, tmp_path):
        mgr = TempFileManager(tmp_dir=str(tmp_path))
        p1 = mgr.create_temp_wav_path()
        p2 = mgr.create_temp_wav_path()
        assert p1 != p2

    def test_cleanup_removes_file(self, tmp_path):
        mgr = TempFileManager(tmp_dir=str(tmp_path))
        path = mgr.create_temp_wav_path()
        with open(path, "wb") as f:
            f.write(b"test")
        assert os.path.exists(path)
        mgr.cleanup(path)
        assert not os.path.exists(path)

    def test_cleanup_silently_ignores_missing_file(self, tmp_path):
        mgr = TempFileManager(tmp_dir=str(tmp_path))
        nonexistent = str(tmp_path / "does-not-exist.wav")
        # should not raise
        mgr.cleanup(nonexistent)

    def test_create_temp_wav_path_under_tmp_dir(self, tmp_path):
        mgr = TempFileManager(tmp_dir=str(tmp_path))
        path = mgr.create_temp_wav_path()
        assert os.path.dirname(path) == str(tmp_path)
