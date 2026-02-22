"""
Base Agent — the only class you need to subclass.

Usage:
    from lisaloop import Agent, GameState, Action, ActionType

    class MyAgent(Agent):
        name = "MyBot"

        def decide(self, state: GameState) -> Action:
            if state.can_check():
                return Action.check()
            return Action.call(state.current_bet)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from lisaloop.core.state import Action, GameState


class Agent(ABC):
    """
    Base class for all poker agents.

    Subclass this and implement `decide()` to create your own poker bot.
    Optionally override `on_hand_start()`, `on_hand_end()`, and `on_opponent_action()`
    for stateful agents that track information across hands.
    """

    name: str = "BaseAgent"
    version: str = "1.0"
    author: str = "Anonymous"
    description: str = ""

    def __init__(self, **kwargs):
        self._hands_played = 0
        self._total_profit = 0.0
        self._config = kwargs

    @abstractmethod
    def decide(self, state: GameState) -> Action:
        """
        Make a decision given the current game state.

        Args:
            state: Complete game state from your perspective. Includes:
                - state.my_hand: your hole cards
                - state.board: community cards
                - state.pot: pot information
                - state.street: current street (PREFLOP, FLOP, TURN, RIVER)
                - state.valid_actions: list of legal actions
                - state.players: info about all players
                - state.position: your position relative to dealer
                - state.history: all actions this hand
                - state.pot_odds: pot odds as ratio
                - state.stack_to_pot_ratio: SPR

        Returns:
            An Action. Use Action.fold(), Action.check(), Action.call(amount),
            Action.bet(amount), Action.raise_to(amount), or Action.all_in(amount).

        Note:
            If you return an invalid action, it will be auto-corrected:
            - Invalid raise → check (if possible) or fold
            - Amount out of range → clamped to valid range
        """
        ...

    def on_hand_start(self, hand_number: int, my_stack: float) -> None:
        """Called at the start of each hand. Override for setup logic."""
        pass

    def on_hand_end(self, result: dict) -> None:
        """
        Called at the end of each hand with results.

        Args:
            result: dict with keys:
                - 'won': bool
                - 'profit': float (positive or negative)
                - 'hand_number': int
                - 'showdown': bool (whether hand went to showdown)
        """
        self._hands_played += 1
        self._total_profit += result.get("profit", 0.0)

    def on_opponent_action(self, player_name: str, action: Action, street: int) -> None:
        """Called when any opponent takes an action. Override to track opponents."""
        pass

    @property
    def stats(self) -> dict:
        return {
            "name": self.name,
            "hands_played": self._hands_played,
            "total_profit": self._total_profit,
            "avg_profit_per_hand": self._total_profit / max(1, self._hands_played),
        }

    def __repr__(self) -> str:
        return f"<{self.name} v{self.version}>"
