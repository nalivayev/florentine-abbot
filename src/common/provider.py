"""Plugin registry and base classes for archive task providers."""

from abc import ABC
from collections.abc import Callable
from importlib.metadata import distributions, entry_points
from pathlib import Path
import sys

_PLUGIN_GROUP = "florentine_abbot.tasks"
_SOURCE_DISTRIBUTION_PATH = Path(__file__).resolve().parents[1]
_providers: dict[str, "ArchiveProvider"] = {}
_loaded = False


class ArchiveProvider(ABC):
    """Base class for archive task providers discovered via entry points."""

    daemon_name: str

    def __init__(self) -> None:
        daemon_name = getattr(self.__class__, "daemon_name", None)
        if not isinstance(daemon_name, str) or not daemon_name:
            raise TypeError(
                f"{self.__class__.__name__} must define a non-empty daemon_name"
            )
        self.daemon_name = daemon_name


def provider(daemon_name: str) -> Callable[[type[ArchiveProvider]], type[ArchiveProvider]]:
    """Declare the daemon name handled by an archive provider class."""

    def decorator(cls: type[ArchiveProvider]) -> type[ArchiveProvider]:
        if not issubclass(cls, ArchiveProvider):
            raise TypeError("@provider can only decorate ArchiveProvider subclasses")
        cls.daemon_name = daemon_name
        return cls

    return decorator


def register_provider_class(provider_class: type[ArchiveProvider]) -> None:
    """Instantiate and register one archive provider class."""
    provider_instance = _build_provider(provider_class)
    _providers[provider_instance.daemon_name] = provider_instance


def _build_provider(provider_class: type[ArchiveProvider]) -> ArchiveProvider:
    if not isinstance(provider_class, type) or not issubclass(provider_class, ArchiveProvider):
        raise TypeError(f"Unsupported archive provider plugin value: {provider_class!r}")
    return provider_class()


def _load_entry_point_providers() -> None:
    seen: set[tuple[str, str]] = set()

    try:
        if sys.version_info >= (3, 10):
            plugins = list(entry_points(group=_PLUGIN_GROUP))
        else:
            eps = entry_points()
            plugins = list(eps.get(_PLUGIN_GROUP, []))  # type: ignore[union-attr]
    except Exception:
        plugins = []

    try:
        for dist in distributions(path=[str(_SOURCE_DISTRIBUTION_PATH)]):
            for ep in dist.entry_points:
                if ep.group == _PLUGIN_GROUP:
                    plugins.append(ep)
    except Exception:
        pass

    for ep in plugins:
        signature = (ep.name, ep.value)
        if signature in seen:
            continue
        seen.add(signature)
        try:
            register_provider_class(ep.load())
        except Exception:
            continue


def load_providers(*, force_reload: bool = False) -> None:
    """Populate the provider registry from built-ins and external plugins."""
    global _loaded

    if _loaded and not force_reload:
        return

    _providers.clear()
    _load_entry_point_providers()
    _loaded = True


def list_providers() -> list[ArchiveProvider]:
    """Return all known archive providers sorted by daemon name."""
    load_providers()
    return sorted(_providers.values(), key=lambda provider: provider.daemon_name)
