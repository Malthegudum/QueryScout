"""Models used by QueryScout."""

import json
from dataclasses import dataclass
from pathlib import Path
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

    def to_csv(self, path: str | Path, **kwargs: Any) -> None:
        """Save the retrieved dataset as CSV."""
        self.data.to_csv(path, index=False, **kwargs)

    def save(self, directory: str | Path) -> Path:
        """Save the dataset and reproducibility metadata to a directory.

        Creates ``data.csv`` and ``query.json``. The standalone Python code is
        stored inside ``query.json`` rather than written as a separate .py file.
        """
        output_dir = Path(directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        self.to_csv(output_dir / "data.csv")

        metadata = {
            "source": self.source,
            "request": self.request.model_dump(exclude_none=True),
            "code": self.code,
        }
        (output_dir / "query.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return output_dir
