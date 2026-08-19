"""MCP tools for Statistics Denmark."""

from queryscout import results

from . import client


def get_dst_subjects():
    """Get Statistics Denmark subject categories."""
    return client.subjects()


def get_dst_tables(subject: str | None = None):
    """Get Statistics Denmark tables, optionally filtered by subject ID."""
    return client.tables(subject)


def get_dst_table_metadata(table_id: str):
    """Get metadata and valid variable/value codes for a table."""
    return client.table(table_id)


def run_dst_query(table_id: str, variables: dict[str, list[str]]):
    """Query a Statistics Denmark table using verified variable/value codes."""
    request, csv_bytes, rows = client.query(table_id, variables)
    code = client.to_python(request)
    power_query = client.to_power_query(request)

    result_id = results.save_result(
        source="dst",
        title=f"Statistics Denmark — {table_id}",
        request=request,
        csv_bytes=csv_bytes,
        code=code,
        power_query=power_query,
        rows=rows,
    )

    return {
        "source": "dst",
        "table_id": table_id,
        "request": request,
        "row_count": len(rows),
        "columns": list(rows[0]) if rows else [],
        "preview": rows[:10],
        "result_url": results.result_url(result_id),
        "result_id": result_id,
    }


def register(mcp):
    mcp.add_tool(
        get_dst_subjects,
        name="get_dst_subjects",
        description="Get Statistics Denmark subject categories.",
    )
    mcp.add_tool(
        get_dst_tables,
        name="get_dst_tables",
        description=(
            "Get Statistics Denmark tables, optionally filtered by subject ID. "
            "Use get_dst_subjects first when you need to narrow the search."
        ),
    )
    mcp.add_tool(
        get_dst_table_metadata,
        name="get_dst_table_metadata",
        description=(
            "Inspect metadata and valid variable/value codes for a Statistics "
            "Denmark table before querying it."
        ),
    )
    mcp.add_tool(
        run_dst_query,
        name="run_dst_query",
        description=(
            "Retrieve data from a Statistics Denmark table. The tool returns a "
            "small preview for validation and a local result URL for the full "
            "CSV plus deterministic Python and Power Query code."
        ),
    )
