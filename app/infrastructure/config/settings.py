"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8012
    assets_dir: str = "./assets"
    tmp_dir: str = "./tmp"
    timeout_sec: int = 120
    max_concurrency: int = 1
    irodori_repo_dir: str | None = None

    model_config = {"env_prefix": "", "case_sensitive": False}
