from dotenv import load_dotenv
from pydantic_ai import Agent

from .models import AgentResult, QueryScoutResult
from .sources.dst.capability import dst_capability
from .sources.dst.client import DSTClient

load_dotenv()

agent = Agent(
    "openai:gpt-5.2",
    output_type=[AgentResult, str],
    capabilities=[dst_capability],
    instructions="""
You are QueryScout, an assistant for retrieving statistical datasets.
Understand what data the user wants and use the available source capabilities to find and verify the correct request.
If the request is sufficiently specified, discover the relevant dataset, inspect its metadata, build and test the request, inspect the preview, revise if needed, and return the exact source, request and standalone Python code from the successful tool result as AgentResult.
If important information is missing or the request is genuinely ambiguous, ask one concise clarification question as plain text instead of guessing.
Never invent the final request or Python code yourself.
""",
)

_SOURCE_CLIENTS = {"dst": DSTClient()}


class QueryNeedsClarification(ValueError):
    def __init__(self, question: str):
        self.question = question
        super().__init__(question)


def print_run(messages) -> None:
    for message in messages:
        for part in message.parts:
            if part.part_kind == "tool-call":
                print(f"→ {part.tool_name}")
                args = part.args_as_dict()
                if args:
                    print(f"  {args}")


def materialize_result(agent_result: AgentResult) -> QueryScoutResult:
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


def query(question: str, verbose: bool = False) -> QueryScoutResult:
    run = agent.run_sync(question)
    if verbose:
        print_run(run.all_messages())
    if isinstance(run.output, str):
        raise QueryNeedsClarification(run.output)
    return materialize_result(run.output)


find_query = query
