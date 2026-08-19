"""QueryScout MCP server."""

from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from queryscout.sources.dst import tools as dst


SOURCES = {
    "dst": {
        "name": "Statistics Denmark",
        "description": "Official Danish statistics from StatBank Denmark.",
        "module": dst,
    },
}

ENABLED_SOURCES: set[str] = set()


def _read_instructions(source_module) -> str:
    return (
        Path(source_module.__file__)
        .with_name("instructions.md")
        .read_text(encoding="utf-8")
        .strip()
    )


def list_sources() -> list[dict[str, object]]:
    """List the statistical APIs available in QueryScout."""
    return [
        {
            "id": source_id,
            "name": source["name"],
            "description": source["description"],
            "enabled": source_id in ENABLED_SOURCES,
        }
        for source_id, source in SOURCES.items()
    ]


async def enable_source(source_id: str, ctx: Context) -> dict[str, object]:
    """Enable one statistical API and expose its tools."""
    source = SOURCES.get(source_id)
    if source is None:
        available = ", ".join(SOURCES)
        raise ValueError(f"Unknown source {source_id!r}. Available: {available}")

    if source_id not in ENABLED_SOURCES:
        source["module"].register(mcp)
        ENABLED_SOURCES.add(source_id)
        await ctx.notify_tools_changed()

    return {
        "id": source_id,
        "name": source["name"],
        "description": source["description"],
        "instructions": _read_instructions(source["module"]),
        "enabled": True,
    }


def create_server() -> MCPServer:
    server = MCPServer(
        "QueryScout",
        instructions=(
            "QueryScout provides access to statistical APIs. "
            "Use queryscout_list_sources to see available sources. "
            "Before using a source, call queryscout_enable_source. "
            "Follow the source-specific instructions returned by that tool."
        ),
        version="0.2.0",
        stateless_http=True,
    )

    server.add_tool(
        list_sources,
        name="queryscout_list_sources",
        description="List the statistical APIs available in QueryScout.",
    )
    server.add_tool(
        enable_source,
        name="queryscout_enable_source",
        description=(
            "Enable one QueryScout source, expose its MCP tools, and return "
            "the source-specific instructions that must be followed."
        ),
    )

    return server


mcp = create_server()


def main() -> None:
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        json_response=True,
    )


if __name__ == "__main__":
    main()
