"""MCP tools for Statistics Denmark."""

import json

from . import client


def search_tables(
    query: str | None = None,
    subject: str | None = None,
    limit: int = 25,
):
    """Search Statistics Denmark tables by text and optional subject."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    tables = client.tables(subject)
    if query:
        needle = query.casefold()
        tables = [
            item
            for item in tables
            if needle in json.dumps(item, ensure_ascii=False).casefold()
        ]
    return tables[:limit]


def get_table(table_id: str):
    """Get metadata and valid variable/value codes for a table."""
    return client.table(table_id)


def query_table(
    table_id: str,
    variables: dict[str, list[str]],
    preview_rows: int = 10,
):
    """Query a verified Statistics Denmark table."""
    if not 1 <= preview_rows <= 50:
        raise ValueError("preview_rows must be between 1 and 50")

    request, rows = client.query(table_id, variables)
    return {
        "source": "dst",
        "table_id": table_id,
        "request": request,
        "row_count": len(rows),
        "columns": list(rows[0]) if rows else [],
        "preview": rows[:preview_rows],
    }


def register(mcp):
    mcp.add_tool(
        search_tables,
        name="dst_search_tables",
        description=(
            "Search Statistics Denmark tables. Use this first when the exact "
            "table ID is unknown."
        ),
    )
    mcp.add_tool(
        get_table,
        name="dst_get_table",
        description=(
            "Inspect metadata and valid codes for a Statistics Denmark table. "
            "Call this before dst_query."
        ),
    )
    mcp.add_tool(
        query_table,
        name="dst_query",
        description=(
            "Retrieve data from a Statistics Denmark table using only verified "
            "table, variable and value codes."
        ),
    )
