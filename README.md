# QueryScout

QueryScout is a small local MCP server for retrieving and transforming
statistical data.

The model chooses sources and transformation parameters. QueryScout performs all
data operations itself and deterministically generates standalone Python that
reproduces the complete pipeline.

## Structure

```text
src/queryscout/
├── server.py
├── instructions.md
├── results.py
├── transforms.py
├── codegen.py
└── sources/
    └── dst.py
```

- `server.py` registers MCP tools and result routes.
- `sources/dst.py` contains the Statistics Denmark integration.
- `transforms.py` contains the allowed filter, select, group-by and join
  operations.
- `results.py` stores datasets, previews and metadata.
- `codegen.py` turns stored pipeline metadata into deterministic `query.py`.

The implementation intentionally uses only a few runtime dependencies:
`mcp`, `pandas` and `requests`.

## Run

```bash
pip install -e .
queryscout
```

The MCP endpoint is:

```text
http://127.0.0.1:8000/mcp
```

## Workflow

A typical workflow is:

```text
source query
    ↓
preview
    ↓
filter/group/join
    ↓
preview
    ↓
next step
    ↓
final result
```

The model sees a compact preview after every step so it can check that the
operation was correct.

Each step creates a result under:

```text
~/.queryscout/results/<result-id>/
├── data.csv
├── metadata.json
└── query.py
```

`metadata.json` contains a simple nested description of the complete pipeline.
`query.py` is generated from that description by QueryScout, not by the model.

## Statistics Denmark

The DST source exposes:

- `get_dst_subjects`
- `get_dst_tables`
- `get_dst_table_metadata`
- `run_dst_query`

Call `enable_source("dst")` before using them.

## Transformations

QueryScout currently exposes:

- `filter_result`
- `select_columns`
- `group_by`
- `join_results`

Each transformation takes existing QueryScout result IDs, writes a new
canonical result, and returns row counts, columns, dtypes and a preview for
validation.

No tool accepts arbitrary Python or SQL.
