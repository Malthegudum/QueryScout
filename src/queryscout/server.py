"""QueryScout MCP server."""

from pathlib import Path

from mcp.server import MCPServer

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
        "Before using a source, call enable_source to load its instructions. "
        "All source tools are already available."
    ),
    version="0.2.0",
)


for module, _ in SOURCES.values():
    module.register(mcp)


def enable_source(source: str) -> str:
    """Return the instructions for a statistical API source."""
    if source not in SOURCES:
        raise ValueError(f"Unknown source: {source}")

    module, _ = SOURCES[source]
    return (
        Path(module.__file__)
        .with_name("instructions.md")
        .read_text(encoding="utf-8")
    )


mcp.add_tool(
    enable_source,
    name="enable_source",
    description="Return instructions for one of the sources listed in the server instructions.",
)


def main() -> None:
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()
