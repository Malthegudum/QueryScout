# QueryScout

QueryScout retrieves statistical datasets from natural-language requests.

The idea is simple: use an AI agent to find and verify the right dataset once, then make the result reusable without the agent. QueryScout currently supports **Statistics Denmark (DST / StatBank)**.

## How it works

```text
Natural-language request
        ↓
    QueryScout
        ↓
find + inspect + test source
        ↓
 verified HTTP request
        ↓
 retrieve dataset
        ↓
 result
 ├── pandas DataFrame
 ├── tested HTTP request
 └── standalone Python code
```

The generated Python uses ordinary `requests` and `pandas`. It does not import QueryScout, so the same dataset can be retrieved later without an LLM.

## Installation

QueryScout requires Python 3.11 or newer.

```bash
git clone https://github.com/Malthegudum/QueryScout.git
cd QueryScout
python -m venv .venv
pip install -e .
```

Activate the virtual environment and create a `.env` file in the project root containing your OpenAI API key.

## Local chat interface

The easiest way to use QueryScout is the local Streamlit chat:

```bash
streamlit run src/queryscout/web/app.py
```

The browser interface lets you describe the dataset you want, answer clarification questions, inspect the resulting table, download it as CSV, and see standalone Python code for retrieving the same data again.

## Python API

```python
from queryscout import query

result = query("Hent Danmarks befolkning fra 2020 og frem")

print(result.data)
print(result.request)
print(result.code)
```

`result.data` is the retrieved pandas `DataFrame`.

Save only the dataset:

```python
result.to_csv("data.csv")
```

Or save the dataset and reproducibility metadata:

```python
result.save("population")
```

This creates:

```text
population/
├── data.csv
└── query.json
```

`query.json` contains the source, tested HTTP request, and standalone Python code.

## Multi-turn conversations

```python
from queryscout import QueryScoutSession

session = QueryScoutSession()

response = session.send("Jeg vil have arbejdsløshed i Danmark")
print(response)

response = session.send("Fordelt på kommuner siden 2020")

if not isinstance(response, str):
    print(response.data)
```

`QueryScoutSession` keeps message history, allowing follow-up messages and clarification questions.

## Architecture

```text
src/queryscout/
├── __init__.py
├── agent.py
├── models.py
├── session.py
├── sources/
│   └── dst/
│       ├── capability.py
│       ├── client.py
│       └── instructions.md
└── web/
    └── app.py
```

The main agent is mostly source-agnostic. Each source owns its API-specific discovery, metadata, request construction, execution, parsing, and standalone-code generation.

The complete dataset is not passed through the language model. The agent discovers and verifies a request; QueryScout then executes that verified request deterministically to produce the final DataFrame.

## Adding another source

A source can follow the same small structure:

```text
sources/
└── example/
    ├── capability.py
    ├── client.py
    └── instructions.md
```

Different APIs do not need to share one universal query model. Each source can use the arguments and parsing logic appropriate for its API.

## Status

QueryScout is an early-stage project focused on making statistical data retrieval simple, verifiable, and reproducible.
