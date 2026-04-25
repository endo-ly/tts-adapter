"""Error response schema (OpenAI-compatible)."""

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    message: str
    type: str
    param: str | None = None
    code: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
