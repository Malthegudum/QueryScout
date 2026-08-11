from pathlib import Path

from pydantic_ai.capabilities import Capability

from .tools import (
    get_dst_subjects,
    get_dst_tables,
    get_dst_table_metadata,
    run_dst_query,
)


instructions = (
    Path(__file__)
    .with_name("instructions.md")
    .read_text(encoding="utf-8")
)


dst_capability = Capability(
    id="dst",
    description=(
        "Statistics Denmark / StatBank. "
        "Use for official Danish statistics such as population, "
        "labour market, prices, businesses and national accounts."
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