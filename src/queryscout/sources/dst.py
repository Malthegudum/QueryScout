"""Statistics Denmark source."""

from io import StringIO

import pandas as pd
import requests

from queryscout import results


BASE_URL = "https://api.statbank.dk/v1"
DESCRIPTION = "Official Danish statistics from StatBank Denmark."

INSTRUCTIONS = """# Statistics Denmark (DST / StatBank)

Use this source for official Danish statistics from Statistics Denmark.

Mandatory workflow:
1. Use get_dst_subjects when the relevant table is not known.
2. Use get_dst_tables to find candidate tables.
3. Use get_dst_table_metadata before every query.
4. Use only table, variable and value codes verified from metadata.
5. Run the smallest query that answers the request.
6. Inspect row count, columns, dtypes and preview after the query.
7. If the result is wrong or unclear, revise the query before transforming it.

Useful DST value syntax:
- "*" selects all values.
- "(1)" selects the newest value where supported.
- Ordered periods can use one range expression such as ">=2020K1<=2024K4".

Never invent DST identifiers or codes. Pay particular attention to measures,
units, geography and time periods.
"""


def subjects():
    response = requests.get(f"{BASE_URL}/subjects", timeout=30)
    response.raise_for_status()
    return response.json()


def tables(subject: str | None = None):
    params = {"subjects": subject} if subject else None
    response = requests.get(f"{BASE_URL}/tables", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def table(table_id: str):
    response = requests.get(
        f"{BASE_URL}/tableinfo",
        params={"id": table_id},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def build_request(
    table_id: str,
    variables: dict[str, list[str]],
) -> dict:
    return {
        "method": "POST",
        "url": f"{BASE_URL}/data",
        "json": {
            "table": table_id,
            "format": "CSV",
            "variables": [
                {"code": code, "values": values}
                for code, values in variables.items()
            ],
        },
    }


def query(
    table_id: str,
    variables: dict[str, list[str]],
) -> tuple[dict, pd.DataFrame]:
    request = build_request(table_id, variables)
    response = requests.request(**request, timeout=60)
    response.raise_for_status()

    dataframe = pd.read_csv(StringIO(response.text), sep=";")
    return request, dataframe


def get_dst_subjects():
    """Get Statistics Denmark subject categories."""
    return subjects()


def get_dst_tables(subject: str | None = None):
    """Get Statistics Denmark tables, optionally filtered by subject ID."""
    return tables(subject)


def get_dst_table_metadata(table_id: str):
    """Get metadata and valid variable/value codes for a table."""
    return table(table_id)


def run_dst_query(
    table_id: str,
    variables: dict[str, list[str]],
):
    """Query a Statistics Denmark table using verified codes."""
    request, dataframe = query(table_id, variables)
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
