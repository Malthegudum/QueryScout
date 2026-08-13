from dotenv import load_dotenv
from pydantic_ai import Agent

from .models import AgentResult, QueryScoutResult
from .sources.dst.capability import dst_capability
from .sources.dst.client import DSTClient

load_dotenv()

agent = Agent(
    "openai:gpt-5.2",
    output_type=AgentResult,
    capabilities=[dst_capability],
    instructions="""
You are QueryScout, an assistant for retrieving statistical datasets.
Understand the dataset the user wants, load the appropriate source, use its tools to discover and test a valid request, inspect the preview, revise if needed, and return the exact source, request and standalone Python code from the successful tool result.
Never invent the final request or Python code yourself.
""",
)

_SOURCE_CLIENTS = {"dst": DSTClient()}


def print_run(messages) -> None:
    for message in messages:
        for part in message.parts:
            if part.part_kind == "tool-call":
                print(f"→ {part.tool_name}")
                args = part.args_as_dict()
                if args:
                    print(f"  {args}")


def query(question: str, verbose: bool = False) -> QueryScoutResult:
    run = agent.run_sync(question)
    if verbose:
        print_run(run.all_messages())
    agent_result = run.output
    try:
        client = _SOURCE_CLIENTS[agent_result.source]
    except KeyError as exc:
        raise ValueError(f"Unsupported data source: {agent_result.source!r}") from exc
    data = client.execute(agent_result.request)
    return QueryScoutResult(
        source=agent_result.source,
        request=agent_result.request,
        code=agent_result.code,
        data=data,
    )


find_query = query
