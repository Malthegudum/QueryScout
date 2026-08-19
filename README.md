# QueryScout

QueryScout is an extensible **Model Context Protocol (MCP) server** for statistical data APIs.

It is designed to run locally and expose well-defined statistical tools to MCP clients such as Open WebUI. QueryScout does not contain its own LLM agent. The model in the MCP client chooses and calls the tools.

Statistics Denmark / StatBank is the first source.

## Architecture

```text
Open WebUI / other MCP client
            |
            | MCP (Streamable HTTP)
            v
       QueryScout
            |
      source registry
       /    |    \
     DST  Eurostat  ...
      |
      v
Statistics Denmark API
```

Each source owns its API client, MCP tools, and instruction set:

```text
src/queryscout/
├── instructions.md
├── registry.py
├── server.py
├── source.py
└── sources/
    └── dst/
        ├── __init__.py
        ├── client.py
        ├── instructions.md
        └── tools.py
```

QueryScout automatically discovers source packages that export a `SOURCE` object.

## Installation

QueryScout requires Python 3.11 or newer.

```bash
git clone https://github.com/Malthegudum/QueryScout.git
cd QueryScout
git checkout mcp-rewrite

python -m venv .venv
```

Activate the environment, then install QueryScout:

```bash
pip install -e .
```

## Run the MCP server

```bash
queryscout
```

or:

```bash
python -m queryscout.server
```

The server listens locally at:

```text
http://127.0.0.1:8000/mcp
```

It uses MCP Streamable HTTP.

### Open WebUI

In Open WebUI, add an external tool server with:

- Type: `MCP (Streamable HTTP)`
- URL: `http://127.0.0.1:8000/mcp`

Open WebUI and QueryScout must be running on the same machine for that URL to work as written.

## Available tools

QueryScout provides two general tools:

- `queryscout_list_sources`
- `queryscout_source_instructions`

The Statistics Denmark source currently provides:

- `dst_search_tables`
- `dst_get_table_metadata`
- `dst_query_table`

The intended DST workflow is:

```text
dst_search_tables
        ↓
dst_get_table_metadata
        ↓
dst_query_table
        ↓
inspect preview and revise if necessary
```

The source-specific instructions explicitly require metadata inspection before querying and prohibit invented table, variable, or value codes.

## Adding another API

Create a new package under `src/queryscout/sources/`:

```text
sources/
└── eurostat/
    ├── __init__.py
    ├── client.py
    ├── instructions.md
    └── tools.py
```

`client.py` contains deterministic API access. `tools.py` contains small, LLM-friendly functions. `instructions.md` contains the workflow and rules that are unique to the API.

The package must export a `SOURCE` object:

```python
from queryscout.source import SourceSpec, ToolSpec

SOURCE = SourceSpec(
    id="example",
    name="Example Statistics API",
    description="What this source is useful for.",
    instructions=instructions,
    tools=(
        ToolSpec(
            name="example_search",
            function=search,
            description="Search datasets in the Example API.",
        ),
    ),
)
```

The registry discovers it automatically at startup. Its instructions are included in the MCP server instructions, and its tools are registered on the server.

## Design principles

- **MCP-first:** QueryScout is a tool server, not a second LLM agent.
- **Source-specific behavior:** each API keeps its own workflow and rules.
- **Verified identifiers:** models should inspect source metadata rather than invent codes.
- **Compact results:** query tools return row counts, columns, previews, exact HTTP requests, and reproducible code instead of pushing whole datasets into model context.
- **Extensible:** adding an API should require a new source package, not changes to the MCP core.

## Status

QueryScout is an early-stage project. The MCP-first rewrite currently focuses on Statistics Denmark as the reference source.
