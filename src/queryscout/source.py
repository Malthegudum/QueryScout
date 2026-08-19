"""Source definitions used by the QueryScout registry."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """One MCP tool exposed by a source."""

    name: str
    function: Callable[..., Any]
    description: str


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """A statistical data source and its source-specific behavior."""

    id: str
    name: str
    description: str
    instructions: str
    tools: tuple[ToolSpec, ...]
