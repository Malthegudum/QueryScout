from typing import Literal

from pydantic import BaseModel


class DSTQuery(BaseModel):
    table_id: str
    variables: dict[str, list[str]]


class DSTQueryResult(BaseModel):
    source: Literal["dst"] = "dst"
    query: DSTQuery