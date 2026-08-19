"""Statistics Denmark source registration."""

from importlib.resources import files

from ...source import SourceSpec, ToolSpec
from .tools import get_table_metadata, query_table, search_tables


instructions = (
    files(__package__)
    .joinpath("instructions.md")
    .read_text(encoding="utf-8")
)

SOURCE = SourceSpec(
    id="dst",
    name="Statistics Denmark",
    description=(
        "Official Danish statistics from Statistics Denmark / StatBank."
    ),
    instructions=instructions,
    tools=(
        ToolSpec(
            name="dst_search_tables",
            function=search_tables,
            description=(
                "Search Statistics Denmark StatBank tables by free text and optional "
                "subject. Use this to discover candidate table IDs before inspecting metadata."
            ),
        ),
        ToolSpec(
            name="dst_get_table_metadata",
            function=get_table_metadata,
            description=(
                "Get metadata for a StatBank table, including variables and valid value "
                "codes. Always use this before querying a table."
            ),
        ),
        ToolSpec(
            name="dst_query_table",
            function=query_table,
            description=(
                "Run a Statistics Denmark StatBank query using only table, variable, and "
                "value codes verified through dst_get_table_metadata. Returns a compact "
                "preview plus the exact request and reproducible Python code."
            ),
        ),
    ),
)
