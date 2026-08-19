"""QueryScout: an extensible MCP server for statistical data APIs."""

from .registry import get_source, get_sources
from .source import SourceSpec, ToolSpec

__all__ = ["SourceSpec", "ToolSpec", "get_source", "get_sources"]
