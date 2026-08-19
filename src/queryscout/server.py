"""QueryScout MCP server."""

from pathlib import Path

from mcp.server import MCPServer

from queryscout.sources.dst import tools as dst


SOURCES = [dst]


def _read_instructions(source_module) -> str:
    return (
        Path(source_module.__file__)
        .with_name("instructions.md")
        .read_text(encoding="utf-8")
        .strip()
    )


def _instructions() -> str:
    base = (
        "QueryScout provides access to statistical APIs.\n"
        "Choose the source that best matches the user's request and follow "
        "that source's instructions."
    )
    source_instructions = "\n\n---\n\n".join(
        _read_instructions(source) for source in SOURCES
    )
    return f"{base}\n\n---\n\n{source_instructions}"


def create_server() -> MCPServer:
    mcp = MCPServer(
        "QueryScout",
        instructions=_instructions(),
        version="0.2.0",
        stateless_http=True,
    )

    for source in SOURCES:
        source.register(mcp)

    return mcp


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
