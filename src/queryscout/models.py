"""Shared models for QueryScout sources."""

from typing import Any

from pydantic import BaseModel


class RequestSpec(BaseModel):
    """Serializable HTTP request description used for reproducibility."""

    method: str
    url: str
    params: dict[str, Any] | None = None
    json: dict[str, Any] | None = None
    headers: dict[str, str] | None = None
