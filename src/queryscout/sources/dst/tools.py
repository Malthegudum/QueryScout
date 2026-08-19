"""MCP-facing tools for Statistics Denmark."""

import json
from typing import Any

from .client import DSTClient


client = DSTClient()


def search_tables(
    query: str | None = None,
    subject: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Search StatBank tables by free text and optional subject."""
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

    tables = client.tables(subject=subject)
    if query:
        needle = query.casefold()
        tables = [
            table
            for table in tables
            if needle in json.dumps(table, ensure_ascii=False).casefold()
        ]
    return tables[:limit]


def get_table_metadata(table_id: str) -> dict[str, Any]:
    """Return metadata, variables, and valid values for a StatBank table."""
    return client.table(table_id)


def query_table(
    table_id: str,
    variables: dict[str, list[str]],
    preview_rows: int = 10,
) -> dict[str, Any]:
    """Run a StatBank query and return a compact, reproducible result."""
    if preview_rows < 1 or preview_rows > 50:
        raise ValueError("preview_rows must be between 1 and 50")

    request = client.build_request(table_id=table_id, variables=variables)
    data = client.execute(request)
    preview = json.loads(
        data.head(preview_rows).to_json(
            orient="records",
            force_ascii=False,
            date_format="iso",
        )
    )

    return {
        "source": "dst",
        "table_id": table_id,
        "request": request.model_dump(exclude_none=True),
        "code": client.to_python(request),
        "row_count": len(data),
        "columns": data.columns.tolist(),
        "preview": preview,
    }
