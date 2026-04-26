"""Application settings loaded from environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings


def _restore_dotenv_windows_path_escapes(value: str | None) -> str | None:
    if value is None:
        return None
    return (
        value
        .replace("\a", r"\a")
        .replace("\b", r"\b")
        .replace("\f", r"\f")
        .replace("\n", r"\n")
        .replace("\r", r"\r")
        .replace("\t", r"\t")
        .replace("\v", r"\v")
    )


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8012
    assets_dir: str = "./assets"
    tmp_dir: str = "./tmp"
    timeout_sec: int = 120
    max_concurrency: int = 1
    irodori_repo_dir: str | None = None

    @field_validator("assets_dir", "tmp_dir", "irodori_repo_dir", mode="before")
    @classmethod
    def restore_dotenv_path_escapes(cls, value: str | None) -> str | None:
        return _restore_dotenv_windows_path_escapes(value)

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
