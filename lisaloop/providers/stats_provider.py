"""
Stats provider — injects session statistics into agent context.

Usage:
    provider = StatsProvider()
    context = provider.get(state, session_stats=stats)
"""

from __future__ import annotations

from typing import Any, Dict

from lisaloop.core.state import GameState
from lisaloop.providers.base import Provider


class StatsProvider(Provider):
    """Provides session statistics and performance metrics."""

    name = "stats"
    description = "Session statistics and performance metrics"

    def __init__(self):
        self._hands_played = 0
        self._total_profit = 0.0
        self._street_counts = {"preflop": 0, "flop": 0, "turn": 0, "river": 0}

    def get(self, state: GameState, **kwargs) -> Dict[str, Any]:
        return {
            "session_hands": self._hands_played,
            "session_profit": self._total_profit,
            "avg_profit_per_hand": self._total_profit / max(1, self._hands_played),
            "hand_number": state.hand_number,
            "street": state.street.name,
        }

    def record_hand(self, profit: float) -> None:
        """Record a completed hand."""
        self._hands_played += 1
        self._total_profit += profit

    def reset(self) -> None:
        """Reset session stats."""
        self._hands_played = 0
        self._total_profit = 0.0
