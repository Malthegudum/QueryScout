"""Models used by QueryScout."""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from pydantic import BaseModel


class RequestSpec(BaseModel):
    method: str
    url: str
    params: dict[str, Any] | None = None
    json: dict[str, Any] | None = None
    headers: dict[str, str] | None = None


class AgentResult(BaseModel):
    source: str
    request: RequestSpec
    code: str


@dataclass(slots=True)
class QueryScoutResult:
    source: str
    request: RequestSpec
    code: str
    data: pd.DataFrame

    @property
    def row_count(self) -> int:
        return len(self.data)

    @property
    def columns(self) -> list[str]:
        return self.data.columns.tolist()

    def preview(self, rows: int = 10) -> pd.DataFrame:
        return self.data.head(rows)
