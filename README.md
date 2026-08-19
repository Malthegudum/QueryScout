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

## Source activation

At startup, QueryScout exposes only:

- `enable_source`

The model calls it with a source ID, for example:

```text
enable_source("dst")
        ↓
DST instructions are returned
        ↓
DST tools become available
```

Available source IDs are listed in the `enable_source` tool description.

## Open WebUI

Add QueryScout as an MCP Streamable HTTP tool server using:

```text
http://127.0.0.1:8000/mcp
```

When a source is enabled, QueryScout sends a tool-list-changed notification so compatible clients can refresh the available tools.

## Statistics Denmark tools

After enabling `dst`, QueryScout exposes:

- `dst_search_tables`
- `dst_get_table`
- `dst_query`

The intended workflow is:

```text
dst_search_tables
        ↓
dst_get_table
        ↓
dst_query
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
    "dst": dst,
    "eurostat": eurostat,
}
```

Also update the `enable_source` tool description so the model can see the new source ID.

No registry, plugin framework, shared source model, or automatic discovery is required.
