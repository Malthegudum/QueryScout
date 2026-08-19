"""QueryScout MCP server."""

from importlib.resources import files

from mcp.server import MCPServer

from .registry import get_source, get_sources


def _global_instructions() -> str:
    return (
        files("queryscout")
        .joinpath("instructions.md")
        .read_text(encoding="utf-8")
        .strip()
    )


def build_server_instructions() -> str:
    """Combine general guidance with every source-specific instruction set."""
    sections = [_global_instructions()]

    for source in get_sources():
        sections.append(
            f"# Source: {source.name} (`{source.id}`)\n\n"
            f"{source.description}\n\n"
            f"{source.instructions.strip()}"
        )

    return "\n\n---\n\n".join(sections)


def list_sources() -> list[dict[str, str]]:
    """List the statistical data sources available through QueryScout."""
    return [
        {
            "id": source.id,
            "name": source.name,
            "description": source.description,
        }
        for source in get_sources()
    ]


def source_instructions(source_id: str) -> dict[str, str]:
    """Return the full instruction set for one QueryScout source."""
    source = get_source(source_id)
    return {
        "id": source.id,
        "name": source.name,
        "description": source.description,
        "instructions": source.instructions,
    }


def create_server() -> MCPServer:
    """Create and populate the QueryScout MCP server."""
    mcp = MCPServer(
        "QueryScout",
        description="Extensible MCP server for official statistical data APIs.",
        instructions=build_server_instructions(),
        version="0.2.0",
    )

    mcp.add_tool(
        list_sources,
        name="queryscout_list_sources",
        description=(
            "List all statistical data sources currently available in QueryScout. "
            "Use this when you are unsure which source is appropriate."
        ),
    )
    mcp.add_tool(
        source_instructions,
        name="queryscout_source_instructions",
        description=(
            "Return the complete source-specific workflow and rules for a QueryScout "
            "source. Use this when you need to review that source's instructions."
        ),
    )

    tool_names: set[str] = {
        "queryscout_list_sources",
        "queryscout_source_instructions",
    }

    for source in get_sources():
        for tool in source.tools:
            if tool.name in tool_names:
                raise ValueError(f"Duplicate MCP tool name: {tool.name}")
            tool_names.add(tool.name)
            mcp.add_tool(
                tool.function,
                name=tool.name,
                description=tool.description,
            )

    return mcp


mcp = create_server()


def main() -> None:
    """Run QueryScout over Streamable HTTP for local MCP clients."""
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()
