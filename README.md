# QueryScout

QueryScout is an experimental AI assistant for querying statistical APIs using natural language.

Instead of asking an LLM to generate arbitrary data-fetching code, QueryScout uses the model to discover and verify a structured query. The resulting query can then be executed again using ordinary Python without involving the AI.

Currently, QueryScout supports **Statistics Denmark (DST / StatBank)**.

## How it works

A user can ask a question such as:

> Get the population of Denmark from 2020 onwards.

QueryScout then:

1. Selects the appropriate data source.
2. Loads the source-specific tools and instructions.
3. Searches for relevant tables.
4. Inspects table metadata.
5. Constructs a structured query.
6. Executes the query and inspects the result.
7. Revises the query if necessary.
8. Returns the verified query and reusable Python code.

Conceptually:

```text
Natural-language question
          ↓
     QueryScout
          ↓
  Data source capability
          ↓
   metadata discovery
          ↓
      DSTQuery
          ↓
    execute + inspect
          ↓
   verified DSTQuery
       ↙       ↘
   dataset    Python code
```

The important distinction is:

- **The agent decides what data to request.**
- **The query describes the request.**
- **The client knows how to execute it.**

Once a query has been found, the AI is no longer required.

## Example

```python
from agent import find_query

result = find_query(
    "Hent Danmarks befolkning fra 2020 og frem",
    verbose=True,
)

print(result.query)
print(result.code)
```

`find_query()` returns:

- the selected data source
- the verified query
- Python code that can execute the same query again

With `verbose=True`, the tool calls made by the agent are also printed.

## Reusing a query without AI

Queries are ordinary Pydantic models.

For Statistics Denmark:

```python
from dst.client import DSTClient
from dst.models import DSTQuery


query = DSTQuery(
    table_id="FOLK1A",
    variables={
        "OMRÅDE": ["000"],
        "Tid": ["2024K1"],
    },
)

client = DSTClient()
data = client.execute(query)

print(data)
```

This makes queries reproducible and usable from notebooks, scripts, or other Python applications without calling an LLM again.

## Architecture

Each statistical data source owns its own implementation:

```text
                        QueryScout
                            │
                    source capability
                            │
              ┌─────────────┼─────────────┐
              │             │             │
             DST       Jobindsats     Eurostat
          (current)      (planned)      (planned)
              │             │             │
           tools          tools          tools
              │             │             │
          DSTQuery          ...           ...
              │
          DSTClient
              │
       Statistics Denmark
```

There is deliberately no generic `DataQuery` or `DataClient`.

Different statistical APIs have different metadata formats, query formats, period conventions, and API behaviour. Each source therefore remains an explicit, self-contained module.

## DST implementation

The current DST integration is structured as:

```text
src/
├── agent.py
└── dst/
    ├── capability.py
    ├── client.py
    ├── codegen.py
    ├── instructions.md
    ├── models.py
    └── tools.py
```

### `models.py`

Defines the reproducible `DSTQuery`.

```python
DSTQuery(
    table_id="...",
    variables={
        "VARIABLE": ["VALUE"],
    },
)
```

### `client.py`

Contains the deterministic Statistics Denmark API integration.

The client can:

- retrieve subjects
- retrieve tables
- retrieve table metadata
- execute a `DSTQuery`

It contains no agent logic.

### `tools.py`

Exposes the DST client to the agent through a small collection of tools:

```text
get_dst_subjects
get_dst_tables
get_dst_table_metadata
run_dst_query
```

The query tool returns a compact preview so the model can inspect the result without requiring the entire dataset in its context.

### `instructions.md`

Contains the source-specific instructions used by the agent when working with Statistics Denmark.

The agent is instructed to inspect metadata, avoid inventing table or value codes, execute its query, and verify the result before returning it.

### `capability.py`

Packages the DST instructions and tools into a Pydantic AI capability.

The capability is loaded on demand, keeping source-specific tools and instructions separate from the main QueryScout agent.

### `codegen.py`

Generates deterministic Python code from a verified `DSTQuery`.

The LLM does not generate this code itself. This ensures that the generated code corresponds exactly to the query that was tested.

## Installation

QueryScout requires Python 3.11 or newer.

Clone the repository:

```bash
git clone https://github.com/Malthegudum/QueryScout.git
cd QueryScout
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

or on macOS/Linux:

```bash
source .venv/bin/activate
```

Install QueryScout in editable mode:

```bash
pip install -e .
```

## OpenAI API key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-api-key
```

The `.env` file should not be committed to Git.

## Development web interface

The Pydantic AI development web interface can be started with:

```bash
python src/agent.py
```

The local server runs at:

```text
http://127.0.0.1:7932
```

The web interface runs the agent directly and is mainly useful for inspecting and debugging agent behaviour.

## Adding another data source

A new data source should be added as its own module rather than modifying the DST implementation.

For example:

```text
src/
├── dst/
│   ├── client.py
│   ├── models.py
│   ├── tools.py
│   ├── capability.py
│   ├── instructions.md
│   └── codegen.py
│
└── jobindsats/
    ├── client.py
    ├── models.py
    ├── tools.py
    ├── capability.py
    ├── instructions.md
    └── codegen.py
```

Each source owns:

- its query model
- its API client
- its agent tools
- its source-specific instructions
- its capability
- its code generation

The main QueryScout agent should only need to know which capabilities are available.

## Project status

QueryScout is currently an early prototype.

Implemented:

- Pydantic AI agent
- on-demand DST capability
- Statistics Denmark metadata discovery
- structured `DSTQuery`
- query execution and result preview
- deterministic reusable Python code generation

Planned:

- additional statistical data sources
- improved query validation
- improved result inspection
- a cleaner user-facing interface