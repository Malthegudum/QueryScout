# QueryScout

QueryScout is an experimental AI assistant for finding and testing queries against statistical APIs from natural-language questions.

Currently, QueryScout supports **Statistics Denmark (DST / StatBank)**.

## Idea

The LLM is used for discovery and interpretation. The final result is deliberately independent of QueryScout.

```text
Natural-language question
        ↓
    QueryScout
        ↓
source-specific capability
        ↓
 internal source query
        ↓
 build + test HTTP request
        ↓
  verified result
   ├── HTTP request
   └── standalone Python code
```

For DST, the agent internally uses `DSTQuery` to navigate StatBank metadata and construct a valid request. That internal model is not the public output.

The public result contains:

- the selected source
- the actual HTTP request that was tested
- standalone Python code using `requests` and `pandas`

The generated code does not import anything from QueryScout.

## Example

```python
from agent import find_query

result = find_query(
    "Hent Danmarks befolkning fra 2020 og frem",
    verbose=True,
)

print(result.request)
print(result.code)
```

With `verbose=True`, QueryScout also prints the tools used during the run.

A result contains the same information conceptually as:

```python
{
    "source": "dst",
    "request": {
        "method": "POST",
        "url": "https://api.statbank.dk/v1/data",
        "json": {
            "table": "...",
            "format": "CSV",
            "variables": [...],
        },
    },
    "code": "...",
}
```

The standalone code is similar to:

```python
from io import StringIO

import pandas as pd
import requests

request = {
    "method": "POST",
    "url": "https://api.statbank.dk/v1/data",
    "json": {...},
}

response = requests.request(**request)
response.raise_for_status()

data = pd.read_csv(StringIO(response.text), sep=";")
```

## Architecture

Each data source owns its own API-specific logic:

```text
                     QueryScout
                         │
                 source capability
                ┌────────┴────────┐
                ↓                 ↓
               DST           Jobindsats
            (current)          (planned)
                │                 │
          internal query     internal query
                │                 │
             client            client
                │                 │
                └────────┬────────┘
                         ↓
                 HTTP request + code
```

There is no shared `DataQuery` or `DataClient`. Different APIs can keep different query models, metadata rules and response parsing.

The only shared output model is a small description of the tested HTTP request.

## DST module

```text
src/
├── agent.py
├── models.py
└── dst/
    ├── capability.py
    ├── client.py
    ├── instructions.md
    ├── models.py
    └── tools.py
```

`DSTClient` owns the deterministic DST-specific work:

- `build_request(query)` converts an internal `DSTQuery` to an HTTP request
- `execute(request)` executes the request and returns a pandas `DataFrame`
- `to_python(request)` creates standalone Python code that performs the same request and parsing

The capability and tools are only used by the agent to discover and verify the correct request.

## Installation

QueryScout requires Python 3.11 or newer.

```bash
git clone https://github.com/Malthegudum/QueryScout.git
cd QueryScout
python -m venv .venv
pip install -e .
```

Activate the environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

or on macOS/Linux:

```bash
source .venv/bin/activate
```

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-api-key
```

## Development web interface

```bash
python src/agent.py
```

The local interface is served at:

```text
http://127.0.0.1:7932
```

## Adding another data source

A new source should provide its own small module, for example:

```text
jobindsats/
├── capability.py
├── client.py
├── instructions.md
├── models.py
└── tools.py
```

The source can use any internal query representation it needs. Its client is responsible for translating that representation into a real HTTP request, executing and parsing the response, and producing standalone Python code.

This keeps QueryScout source-specific internally while making its final output portable.
