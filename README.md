# QueryScout

QueryScout is a small local **Model Context Protocol (MCP) server** for statistical APIs.

The model in the MCP client, such as Open WebUI, chooses and calls the tools. QueryScout itself does not contain an LLM agent.

Statistics Denmark / StatBank is the first source.

## Structure

```text
src/queryscout/
├── server.py
└── sources/
    └── dst/
        ├── client.py
        ├── tools.py
        └── instructions.md
```

Each source has only three files:

- `client.py` — direct API calls
- `tools.py` — MCP tools and registration
- `instructions.md` — source-specific workflow and rules

## Installation

QueryScout requires Python 3.11 or newer.

```bash
git clone https://github.com/Malthegudum/QueryScout.git
cd QueryScout
git checkout mcp-rewrite
python -m venv .venv
```

Activate the environment and install QueryScout:

```bash
pip install -e .
```

The runtime dependencies are intentionally small:

- `mcp`
- `requests`

## Run

```bash
queryscout
```

or:

```bash
python -m queryscout.server
```

The MCP endpoint is:

```text
http://127.0.0.1:8000/mcp
```

It uses MCP Streamable HTTP.

## Sources and tools

All source tools are registered when QueryScout starts, so MCP clients such as Open WebUI can see them immediately.

QueryScout also exposes:

- `enable_source`

`enable_source` does not register tools. It only returns the selected source's `instructions.md`, so the model can follow the source-specific workflow and rules.

For example:

```text
enable_source("dst")
        ↓
DST instructions are returned
        ↓
use the already-available DST tools
```

The server instructions include a short list of all available sources and descriptions.

## Open WebUI

Add QueryScout as an MCP Streamable HTTP tool server using:

```text
http://127.0.0.1:8000/mcp
```

Because all source tools are registered at startup, Open WebUI does not need to refresh the MCP tool list after `enable_source` is called.

## Statistics Denmark tools

The DST source exposes:

- `get_dst_subjects`
- `get_dst_tables`
- `get_dst_table_metadata`
- `run_dst_query`

The intended workflow is:

```text
get_dst_subjects
        ↓
get_dst_tables
        ↓
get_dst_table_metadata
        ↓
run_dst_query
        ↓
inspect the result and revise if necessary
```

The source instructions require metadata inspection before querying and prohibit invented table IDs, variable codes, and value codes.

## Adding another API

Create another source directory with the same three-file structure:

```text
src/queryscout/sources/eurostat/
├── client.py
├── tools.py
└── instructions.md
```

Then import its `tools` module in `server.py` and add one entry to `SOURCES`:

```python
from queryscout.sources.dst import tools as dst
from queryscout.sources.eurostat import tools as eurostat

SOURCES = {
    "dst": (dst, "Official Danish statistics from StatBank Denmark."),
    "eurostat": (eurostat, "Official European Union statistics."),
}
```

All tools registered by the new source's `register(mcp)` function will then be available when QueryScout starts.

No registry, plugin framework, shared source model, or automatic discovery is required.
