"""Subprocess runner for Irodori CLI execution."""

import asyncio

from app.domain.errors import ProviderExecutionError, ProviderTimeoutError
from app.infrastructure.logging.logger import logger


class SubprocessRunner:
    def __init__(self, timeout_sec: int = 120) -> None:
        self._timeout = timeout_sec

    async def run(self, cmd: list[str], cwd: str | None = None) -> str:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise ProviderTimeoutError("irodori")
        except OSError as e:
            raise ProviderExecutionError("irodori", str(e)) from e

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            detail = stderr.strip() or stdout.strip() or f"exit code {proc.returncode}"
            raise ProviderExecutionError("irodori", detail)

        if stdout.strip():
            logger.debug("Irodori stdout: %s", stdout.strip())
        if stderr.strip():
            logger.debug("Irodori stderr: %s", stderr.strip())

        return stdout
