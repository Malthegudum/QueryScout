# QueryScout

QueryScout is a small local **Model Context Protocol (MCP) server** for statistical APIs.

The model in the MCP client, such as Open WebUI, chooses and calls the tools. QueryScout itself does not contain an LLM agent.

Statistics Denmark / StatBank is the first source.

## Structure

```text
src/queryscout/
├── instructions.md
├── results.py
├── server.py
└── sources/
    └── dst/
        ├── client.py
        ├── tools.py
        └── instructions.md
```

Each source has only three files:

- `client.py` — direct API calls and deterministic request/code generation
- `tools.py` — MCP tools and registration
- `instructions.md` — source-specific workflow and rules

`results.py` is shared infrastructure for storing query outputs and rendering local result pages.

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

QueryScout also exposes `enable_source`. It only returns the selected source's `instructions.md`; the server instructions require the model to call it before using that source's tools.

## Query results

QueryScout deliberately separates model validation from the full output.

`run_dst_query` returns only a compact result to the model:

- the exact request;
- row count;
- column names;
- a 10-row preview;
- a local `result_url`.

The model uses that preview to check whether the query returned the intended concepts, units, geography and periods. If the preview looks wrong, it should revise the query.

The full result is stored locally under:

```text
~/.queryscout/results/<result-id>/
├── data.csv
├── metadata.json
└── query.py
```

The full CSV and deterministic Python code are **not** included in the MCP tool result. They are served directly by QueryScout at:

```text
http://127.0.0.1:8000/results/<result-id>
```

The result page shows a larger preview, the exact request and generated Python code, with direct downloads for `data.csv` and `query.py`.

The result ID is derived from the exact request and returned CSV bytes, so a changed dataset produces a different result ID even if the query is otherwise unchanged.

## Open WebUI

Add QueryScout as an MCP Streamable HTTP tool server using:

```text
http://127.0.0.1:8000/mcp
```

Because all source tools are registered at startup, Open WebUI does not need to refresh the MCP tool list after `enable_source` is called.

After a successful query, the model can validate the compact preview and provide the local QueryScout result URL. Opening that URL displays the result UI directly from QueryScout rather than sending the full dataset or Python code through the model.

## Statistics Denmark tools

The DST source exposes:

- `get_dst_subjects`
- `get_dst_tables`
- `get_dst_table_metadata`
- `run_dst_query`

The intended workflow is:

```text
enable_source("dst")
        ↓
get_dst_subjects
        ↓
get_dst_tables
        ↓
get_dst_table_metadata
        ↓
run_dst_query
        ↓
validate the compact preview
        ↓
open the local result page
```

## Deterministic Python code

DST queries are represented as ordinary request dictionaries. `client.py` deterministically converts the exact executed request into standalone Python code. No LLM generates or rewrites that code.

The generated script replays the same HTTP request and writes the returned bytes to `data.csv`.

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

A new source can reuse `queryscout.results.save_result(...)` to get the same local result page/download behavior.

No registry, plugin framework, shared source model, or automatic discovery is required.
