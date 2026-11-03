"""Provider plugin registry for Energy-UA Power Off.

To add a provider, create a module with a BaseProvider subclass and list it
in PROVIDERS below.
"""
from __future__ import annotations

from .base import BaseProvider
from .energy_ua import EnergyUAProvider
from .zoe import ZOEProvider

PROVIDERS: dict[str, type[BaseProvider]] = {
    cls.key: cls for cls in (ZOEProvider, EnergyUAProvider)
}


def get_providers() -> dict[str, type[BaseProvider]]:
    """Return the provider registry."""
    return PROVIDERS


def get_provider(key: str) -> type[BaseProvider]:
    """Return a provider class by its key."""
    if key not in PROVIDERS:
        raise KeyError(f"Unknown provider: {key!r}. Available: {list(PROVIDERS)}")
    return PROVIDERS[key]
