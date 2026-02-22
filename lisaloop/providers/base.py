"""
Provider base class — injectable context for agent decisions.

Providers compute and inject additional context that agents can use.
They separate "what data is available" from "how agents use it".

Usage:
    from lisaloop.providers import Provider

    class MyProvider(Provider):
        name = "my-data"

        def get(self, state, **kwargs):
            return {"custom_metric": compute_something(state)}
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from lisaloop.core.state import GameState


class Provider(ABC):
    """
    Base class for context providers.

    A provider computes additional information from game state
    and makes it available to agents and other framework components.
    """

    name: str = "base-provider"
    description: str = ""

    @abstractmethod
    def get(self, state: GameState, **kwargs) -> Dict[str, Any]:
        """
        Compute and return context data.

        Args:
            state: Current game state
            **kwargs: Additional context (agent info, history, etc.)

        Returns:
            Dict of computed context data
        """
        ...

    def __repr__(self) -> str:
        return f"Provider('{self.name}')"
