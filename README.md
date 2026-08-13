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

## Architecture

Each data source owns its own API-specific logic.

```text
src/
├── agent.py
├── models.py
└── dst/
    ├── capability.py
    ├── client.py
    ├── instructions.md
    └── models.py
```

`capability.py` contains the DST tools and packages them into the on-demand Pydantic AI capability.

`DSTClient` owns the deterministic DST-specific work:

- `build_request(query)` converts an internal `DSTQuery` to an HTTP request
- `execute(request)` executes the request and returns a pandas `DataFrame`
- `to_python(request)` creates standalone Python code that performs the same request and parsing

There is no shared `DataQuery` or `DataClient`. Different APIs can keep different query models, metadata rules and response parsing.

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

The local interface is served at `http://127.0.0.1:7932`.

## Adding another data source

A new source should provide its own small module, for example:

```text
jobindsats/
├── capability.py
├── client.py
├── instructions.md
└── models.py
```

The source can use any internal query representation it needs. Its client is responsible for translating that representation into a real HTTP request, executing and parsing the response, and producing standalone Python code.
