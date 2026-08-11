from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent

from dst.capability import dst_capability
from dst.codegen import query_to_python
from dst.models import DSTQuery, DSTQueryResult


load_dotenv()


QueryScoutOutput = DSTQueryResult


class QueryScoutResult(BaseModel):
    source: Literal["dst"]
    query: DSTQuery
    code: str


agent = Agent(
    "openai:gpt-5.2",
    output_type=QueryScoutOutput,
    capabilities=[
        dst_capability,
    ],
    instructions="""
You are QueryScout, an assistant for retrieving statistical datasets.

Your job is to:
1. Understand what dataset the user wants.
2. Choose the most appropriate available data source.
3. Load that data source's capability.
4. Follow its source-specific instructions.
5. Use its tools to find a valid query.
6. Run and inspect the query.
7. Revise the query if necessary.
8. Return the exact query that you successfully tested.

Do not invent table IDs, variables or values.

Only return a query after it has been successfully tested.
""",
)


def print_run(messages):
    for message in messages:
        for part in message.parts:
            if part.part_kind == "tool-call":
                print(f"→ {part.tool_name}")

                args = part.args_as_dict()

                if args:
                    print(f"  {args}")


def find_query(
    question: str,
    verbose: bool = False,
) -> QueryScoutResult:
    result = agent.run_sync(question)

    if verbose:
        print_run(result.all_messages())

    output = result.output

    if output.source == "dst":
        code = query_to_python(output.query)
    else:
        raise ValueError(f"Unsupported source: {output.source}")

    return QueryScoutResult(
        source=output.source,
        query=output.query,
        code=code,
    )


if __name__ == "__main__":
    import uvicorn

    app = agent.to_web()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=7932,
    )