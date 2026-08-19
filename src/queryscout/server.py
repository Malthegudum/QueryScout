"""QueryScout MCP server."""

from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from queryscout.sources.dst import tools as dst


SOURCES = {
    "dst": (dst, "Official Danish statistics from StatBank Denmark."),
}

SOURCE_LIST = "\n".join(
    f"- {name}: {description}"
    for name, (_, description) in SOURCES.items()
)

mcp = MCPServer(
    "QueryScout",
    instructions=(
        "QueryScout provides access to statistical APIs.\n\n"
        f"Available sources:\n{SOURCE_LIST}\n\n"
        "Choose a source with enable_source, then follow the returned instructions."
    ),
    version="0.2.0",
    stateless_http=True,
)


async def enable_source(source: str, ctx: Context) -> str:
    """Enable a statistical API and return its instructions."""
    if source not in SOURCES:
        raise ValueError(f"Unknown source: {source}")

    module, _ = SOURCES[source]
    module.register(mcp)
    await ctx.notify_tools_changed()

    return (
        Path(module.__file__)
        .with_name("instructions.md")
        .read_text(encoding="utf-8")
    )


mcp.add_tool(
    enable_source,
    name="enable_source",
    description="Enable one of the sources listed in the server instructions.",
)


def main() -> None:
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        json_response=True,
    )


if __name__ == "__main__":
    main()
