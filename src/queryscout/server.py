"""QueryScout MCP server."""

from pathlib import Path

from mcp.server import MCPServer
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, PlainTextResponse

from queryscout import results, transforms
from queryscout.sources.dst import tools as dst


SOURCES = {
    "dst": dst,
}

SOURCE_LIST = "\n".join(
    f"- {name}: {module.DESCRIPTION}"
    for name, module in SOURCES.items()
)

SERVER_INSTRUCTIONS = Path(__file__).with_name("instructions.md").read_text(
    encoding="utf-8"
)

mcp = MCPServer(
    "QueryScout",
    instructions=f"{SERVER_INSTRUCTIONS}\n\nAvailable sources:\n{SOURCE_LIST}",
    version="0.3.0",
)


for module in SOURCES.values():
    module.register(mcp)

transforms.register(mcp)


def enable_source(source: str) -> str:
    """Return the instructions for a statistical API source."""
    if source not in SOURCES:
        raise ValueError(f"Unknown source: {source}")

    module = SOURCES[source]
    return (
        Path(module.__file__)
        .with_name("instructions.md")
        .read_text(encoding="utf-8")
    )


mcp.add_tool(
    enable_source,
    name="enable_source",
    description=(
        "Load the mandatory instructions for one source before using any of "
        "that source's tools."
    ),
)


@mcp.custom_route("/results/{result_id}", methods=["GET"])
async def result_page(request: Request):
    result_id = request.path_params["result_id"]
    try:
        page = results.render_result_page(result_id)
    except FileNotFoundError:
        return PlainTextResponse("Result not found.", status_code=404)

    return HTMLResponse(page, headers={"Content-Disposition": "inline"})


@mcp.custom_route("/results/{result_id}/data.csv", methods=["GET"])
async def download_data(request: Request):
    result_id = request.path_params["result_id"]
    try:
        path = results.result_file(result_id, "data.csv")
    except FileNotFoundError:
        return PlainTextResponse("Result not found.", status_code=404)

    return FileResponse(path, media_type="text/csv", filename="data.csv")


@mcp.custom_route("/results/{result_id}/query.py", methods=["GET"])
async def download_code(request: Request):
    result_id = request.path_params["result_id"]
    try:
        path = results.result_file(result_id, "query.py")
    except FileNotFoundError:
        return PlainTextResponse("Result not found.", status_code=404)

    return FileResponse(path, media_type="text/x-python", filename="query.py")


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
