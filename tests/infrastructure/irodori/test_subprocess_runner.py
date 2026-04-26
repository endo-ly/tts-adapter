"""Tests for Irodori SubprocessRunner."""

import asyncio

import pytest

from app.domain.errors import ProviderExecutionError, ProviderTimeoutError
from app.infrastructure.providers.irodori.subprocess_runner import SubprocessRunner


class TestSubprocessRunner:
    async def test_run_success_returns_stdout(self):
        runner = SubprocessRunner(timeout_sec=10)
        stdout = await runner.run(["echo", "hello"])
        assert "hello" in stdout

    async def test_run_nonzero_exit_raises_execution_error(self):
        runner = SubprocessRunner(timeout_sec=10)
        with pytest.raises(ProviderExecutionError) as exc_info:
            await runner.run(["false"])
        assert exc_info.value.provider_name == "irodori"

    async def test_run_timeout_raises_timeout_error(self):
        runner = SubprocessRunner(timeout_sec=0.5)
        with pytest.raises(ProviderTimeoutError):
            await runner.run(["sleep", "5"])

    async def test_run_captures_stderr_in_error(self):
        runner = SubprocessRunner(timeout_sec=10)
        with pytest.raises(ProviderExecutionError) as exc_info:
            await runner.run(["bash", "-c", "echo 'error msg' >&2; exit 1"])
        assert "error msg" in exc_info.value.detail

    async def test_run_wraps_os_error(self):
        runner = SubprocessRunner(timeout_sec=10)
        with pytest.raises(ProviderExecutionError) as exc_info:
            await runner.run(["echo", "hello"], cwd="/path/that/does/not/exist")
        assert exc_info.value.provider_name == "irodori"

    async def test_run_with_list_str_not_shell(self):
        """Verify runner uses list[str] args, not shell=True."""
        runner = SubprocessRunner(timeout_sec=10)
        # If it used shell=True, this would be interpreted as a shell command
        stdout = await runner.run(["echo", "hello world"])
        assert "hello world" in stdout
