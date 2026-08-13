"""Shared output models used by QueryScout across data sources."""

from typing import Any

from pydantic import BaseModel


class RequestSpec(BaseModel):
    """Portable description of a tested HTTP request.

    Source-specific clients create this model after translating their own API
    parameters into an ordinary HTTP request. Keeping it transport-level makes
    the final result reusable outside QueryScout.
    """

    method: str
    url: str
    params: dict[str, Any] | None = None
    json: dict[str, Any] | None = None
    headers: dict[str, str] | None = None


class QueryScoutResult(BaseModel):
    """Public result returned by the QueryScout agent."""

    # Name of the source that produced and verified the request, e.g. "dst".
    source: str

    # Exact HTTP request that was successfully tested by the source capability.
    request: RequestSpec

    # Standalone Python code for repeating the request without QueryScout.
    code: str
