"""
Equity provider — injects real-time equity calculations into agent context.

Usage:
    provider = EquityProvider(iterations=5000)
    context = provider.get(state)
    print(context["equity"])  # 0.65 (65% equity vs random hand)
"""

from __future__ import annotations

from typing import Any, Dict

from lisaloop.core.state import GameState
from lisaloop.providers.base import Provider


class EquityProvider(Provider):
    """Provides real-time equity estimates for the current hand."""

    name = "equity"
    description = "Monte Carlo equity calculation"

    def __init__(self, iterations: int = 5000, seed: int | None = None):
        self._iterations = iterations
        self._seed = seed

    def get(self, state: GameState, **kwargs) -> Dict[str, Any]:
        from lisaloop.equity import EquityCalculator

        calc = EquityCalculator(seed=self._seed)

        hand_str = str(state.my_hand.cards[0]) + str(state.my_hand.cards[1])
        board_str = "".join(str(c) for c in state.board)

        # Estimate equity vs a random hand
        try:
            result = calc.evaluate(
                hand_str, "22+",
                board=board_str,
                iterations=self._iterations,
            )
            equity = result.equities[0]
        except Exception:
            equity = 0.5

        return {
            "equity": equity,
            "hand": hand_str,
            "board": board_str,
        }
