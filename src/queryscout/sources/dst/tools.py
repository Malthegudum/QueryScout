"""MCP tools for Statistics Denmark."""

from queryscout import results

from . import client


DESCRIPTION = "Official Danish statistics from StatBank Denmark."


def get_dst_subjects():
    """Get Statistics Denmark subject categories."""
    return client.subjects()


def get_dst_tables(subject: str | None = None):
    """Get Statistics Denmark tables, optionally filtered by subject ID."""
    return client.tables(subject)


def get_dst_table_metadata(table_id: str):
    """Get metadata and valid variable/value codes for a table."""
    return client.table(table_id)


def run_dst_query(
    table_id: str,
    variables: dict[str, list[str]],
):
    """Query a Statistics Denmark table using verified codes."""
    request, dataframe = client.query(table_id, variables)
    pipeline = {
        "type": "source",
        "source": "dst",
        "request": request,
    }

    result_id = results.save_result(
        title=f"Statistics Denmark — {table_id}",
        dataframe=dataframe,
        pipeline=pipeline,
    )

    return results.result_summary(
        result_id,
        extra={
            "source": "dst",
            "table_id": table_id,
            "request": request,
        },
    )


def register(mcp) -> None:
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
            "Use get_dst_subjects first when needed."
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
            "Retrieve a Statistics Denmark dataset and return a compact "
            "validation preview plus a local result URL."
        ),
    )
