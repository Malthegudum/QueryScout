"""Automatic discovery of QueryScout source packages."""

from functools import lru_cache
from importlib import import_module
from pkgutil import iter_modules

from .source import SourceSpec
from . import sources as sources_package


@lru_cache(maxsize=1)
def get_sources() -> tuple[SourceSpec, ...]:
    """Discover source packages that export a ``SOURCE`` object."""
    discovered: list[SourceSpec] = []

    for module_info in iter_modules(
        sources_package.__path__,
        prefix=f"{sources_package.__name__}.",
    ):
        if not module_info.ispkg:
            continue

        module = import_module(module_info.name)
        source = getattr(module, "SOURCE", None)
        if source is None:
            continue
        if not isinstance(source, SourceSpec):
            raise TypeError(
                f"{module_info.name}.SOURCE must be a SourceSpec, "
                f"got {type(source).__name__}"
            )
        discovered.append(source)

    ids = [source.id for source in discovered]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate QueryScout source IDs are not allowed.")

    return tuple(sorted(discovered, key=lambda source: source.id))


def get_source(source_id: str) -> SourceSpec:
    """Return one registered source by ID."""
    for source in get_sources():
        if source.id == source_id:
            return source
    available = ", ".join(source.id for source in get_sources()) or "none"
    raise ValueError(f"Unknown source {source_id!r}. Available sources: {available}")
