"""Main QueryScout agent and simple Python entry point."""

from dotenv import load_dotenv
from pydantic_ai import Agent

from dst.capability import dst_capability
from models import QueryScoutResult


# Load environment variables, including the OpenAI API key, before creating the agent.
load_dotenv()


# The main agent stays source-agnostic. Source-specific behavior is loaded through
# deferred capabilities such as the DST capability below.
agent = Agent(
    "openai:gpt-5.2",
    output_type=QueryScoutResult,
    capabilities=[
        dst_capability,
    ],
    instructions="""
You are QueryScout, an assistant for retrieving statistical datasets.

Your job is to:
1. Understand what dataset the user wants.
2. Choose and load the most appropriate available data source.
3. Follow that source's instructions.
4. Use its tools to discover and test a valid request.
5. Inspect the returned data preview.
6. Revise the request if necessary.
7. Return the source, request and standalone Python code from the
   successful tool result.

Never invent the final request or Python code yourself.
Only return values produced by a successfully tested source tool.
""",
)


def print_run(messages):
    """Print tool calls from an agent run for lightweight debugging."""
    for message in messages:
        for part in message.parts:
            # Only tool calls are useful here; regular model messages are omitted.
            if part.part_kind == "tool-call":
                print(f"→ {part.tool_name}")

                args = part.args_as_dict()

                if args:
                    print(f"  {args}")


def find_query(
    question: str,
    verbose: bool = False,
) -> QueryScoutResult:
    """Find and verify a statistical API request for a natural-language question.

    Args:
        question: Description of the statistical data to retrieve.
        verbose: Print the agent's tool calls when true.

    Returns:
        The verified source, HTTP request and standalone Python code.
    """
    # run_sync is the simple synchronous interface used by scripts and notebooks.
    result = agent.run_sync(question)

    if verbose:
        print_run(result.all_messages())

    return result.output


if __name__ == "__main__":
    import uvicorn

    # Pydantic AI can expose the same agent through a small development web UI.
    app = agent.to_web()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=7932,
    )
