"""Pydantic AI capability for Statistics Denmark."""

from pathlib import Path

from pydantic_ai.capabilities import Capability

from .client import DSTClient


client = DSTClient()


def get_dst_subjects():
    return client.subjects()


def get_dst_tables(subject: str | None = None):
    return client.tables(subject)


def get_dst_table_metadata(table_id: str):
    return client.table(table_id)


def run_dst_query(table_id: str, variables: dict[str, list[str]]):
    request = client.build_request(table_id=table_id, variables=variables)
    data = client.execute(request)
    return {
        "source": "dst",
        "request": request.model_dump(exclude_none=True),
        "code": client.to_python(request),
        "row_count": len(data),
        "columns": data.columns.tolist(),
        "preview": data.head(10).to_dict(orient="records"),
    }


instructions = Path(__file__).with_name("instructions.md").read_text(encoding="utf-8")


dst_capability = Capability(
    id="dst",
    description=(
        "Statistics Denmark / StatBank. Use for official Danish statistics such as "
        "population, labour market, prices, businesses and national accounts."
    ),
    instructions=instructions,
    tools=[
        get_dst_subjects,
        get_dst_tables,
        get_dst_table_metadata,
        run_dst_query,
    ],
    defer_loading=True,
)
