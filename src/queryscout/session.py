"""Conversation state for multi-turn QueryScout use."""

from typing import Any

from .agent import agent, materialize_result, print_run
from .models import QueryScoutResult


class QueryScoutSession:
    """Stateful QueryScout conversation."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._messages: list[Any] = []

    @property
    def messages(self) -> list[Any]:
        return list(self._messages)

    def reset(self) -> None:
        self._messages = []

    def send(self, message: str) -> str | QueryScoutResult:
        run = agent.run_sync(message, message_history=self._messages or None)
        self._messages = run.all_messages()

        if self.verbose:
            print_run(run.new_messages())

        if isinstance(run.output, str):
            return run.output

        return materialize_result(run.output)
