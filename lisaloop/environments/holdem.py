"""
Texas Hold'em environment — standard 6-max cash game.

Usage:
    from lisaloop.environments import HoldemEnvironment
    from lisaloop.agents import LisaAgent, TAGAgent

    env = HoldemEnvironment(seats=6, small_blind=0.25, big_blind=0.50)
    env.add_agent(LisaAgent(seed=42))
    env.add_agent(TAGAgent(seed=42))

    results = env.run(hands=5000)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from lisaloop.environments.base import GameEnvironment, EnvConfig
from lisaloop.core.table import Table, TableConfig, HandResult


@dataclass
class HoldemConfig(EnvConfig):
    name: str = "holdem-6max"
    max_players: int = 6
    small_blind: float = 0.25
    big_blind: float = 0.50
    starting_stack: float = 100.0
    rebuy: bool = True
    rebuy_threshold: float = 20.0


class HoldemEnvironment(GameEnvironment):
    """
    Texas Hold'em 6-max cash game environment.

    Standard cash game rules with optional rebuys. Wraps the
    core Table simulation with the environment interface.
    """

    def __init__(self, config: HoldemConfig | None = None, **kwargs):
        cfg = config or HoldemConfig(**kwargs)
        super().__init__(cfg)
        self._holdem_config: HoldemConfig = cfg
        self._table: Optional[Table] = None
        self._hands_played = 0

    def reset(self) -> None:
        """Reset the table with current agents."""
        self._table = Table(TableConfig(
            num_seats=self._holdem_config.max_players,
            small_blind=self._holdem_config.small_blind,
            big_blind=self._holdem_config.big_blind,
            seed=self._holdem_config.seed,
        ))

        for i, agent in enumerate(self._agents):
            self._table.seat_player(
                i, agent, name=agent.name,
                stack=self._holdem_config.starting_stack,
            )

        self._hands_played = 0

    def step(self) -> HandResult:
        """Play one hand. Returns HandResult."""
        if self._table is None:
            self.reset()

        # Rebuy if needed
        if self._holdem_config.rebuy:
            for seat, info in self._table.seats.items():
                if info.stack < self._holdem_config.rebuy_threshold:
                    info.stack = self._holdem_config.starting_stack

        result = self._table.play_hand()
        self._hands_played += 1
        return result

    def get_state(self) -> Dict[str, Any]:
        """Get current environment state."""
        if not self._table:
            return {"status": "not started"}

        return {
            "environment": self._holdem_config.name,
            "hands_played": self._hands_played,
            "players": {
                info.name: {"stack": info.stack, "seat": seat}
                for seat, info in self._table.seats.items()
            },
            "blinds": f"${self._holdem_config.small_blind}/${self._holdem_config.big_blind}",
        }
