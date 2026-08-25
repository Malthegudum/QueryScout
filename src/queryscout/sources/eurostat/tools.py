"""MCP tools for Eurostat."""

from queryscout import results

from . import client


DESCRIPTION = "Official European statistics from Eurostat."


def search_eurostat_datasets(query: str, limit: int = 20):
    """Search Eurostat datasets by title or dataset code."""
    return client.search_datasets(query, limit=limit)


def get_eurostat_dataset_metadata(dataset_code: str):
    """Get dimensions and a compact preview of valid codes for a dataset."""
    return client.dataset_metadata(dataset_code)


def get_eurostat_dimension_values(
    dataset_code: str,
    dimension: str,
    query: str | None = None,
    limit: int = 100,
):
    """Get or search valid values for one Eurostat dataset dimension."""
    return client.dimension_values(
        dataset_code,
        dimension,
        query=query,
        limit=limit,
    )


def run_eurostat_query(
    dataset_code: str,
    dimensions: dict[str, list[str]],
    start_period: str | None = None,
    end_period: str | None = None,
):
    """Query Eurostat using dimension codes verified from metadata."""
    request, dataframe = client.query(
        dataset_code,
        dimensions,
        start_period=start_period,
        end_period=end_period,
    )
    pipeline = {
        "type": "source",
        "source": "eurostat",
        "request": request,
        "parser": {
            "type": "csv",
            "kwargs": {},
        },
    }

    result_id = results.save_result(
        title=f"Eurostat — {dataset_code.upper()}",
        dataframe=dataframe,
        pipeline=pipeline,
    )

    return results.result_summary(
        result_id,
        extra={
            "source": "eurostat",
            "dataset_code": dataset_code.upper(),
            "request": request,
        },
    )


def register(mcp) -> None:
    mcp.add_tool(
        search_eurostat_datasets,
        name="search_eurostat_datasets",
        description=(
            "Search Eurostat datasets by title or code. Use this when the "
            "dataset code is not already known."
        ),
    )
    mcp.add_tool(
        get_eurostat_dataset_metadata,
        name="get_eurostat_dataset_metadata",
        description=(
            "Inspect a Eurostat dataset's dimensions and compact previews of "
            "valid dimension values before querying it."
        ),
    )
    mcp.add_tool(
        get_eurostat_dimension_values,
        name="get_eurostat_dimension_values",
        description=(
            "List or search valid values for one Eurostat dimension. Use this "
            "when metadata reports that the value preview is truncated."
        ),
    )
    mcp.add_tool(
        run_eurostat_query,
        name="run_eurostat_query",
        description=(
            "Retrieve a Eurostat dataset slice using verified dimension codes "
            "and return a compact validation preview plus a local result URL."
        ),
    )
