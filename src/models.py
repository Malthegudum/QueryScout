from typing import Any

from pydantic import BaseModel


class RequestSpec(BaseModel):
    method: str
    url: str
    params: dict[str, Any] | None = None
    json: dict[str, Any] | None = None
    headers: dict[str, str] | None = None


class QueryScoutResult(BaseModel):
    source: str
    request: RequestSpec
    code: str
