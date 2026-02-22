"""
Heads-up environment — optimized for 1v1 matches.

Usage:
    from lisaloop.environments import HeadsUpEnvironment
    from lisaloop.agents import LisaAgent, TAGAgent

    env = HeadsUpEnvironment(small_blind=0.50, big_blind=1.00)
    env.add_agent(LisaAgent(seed=42))
    env.add_agent(TAGAgent(seed=42))

    results = env.run(hands=10000)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from lisaloop.environments.holdem import HoldemConfig, HoldemEnvironment


@dataclass
class HeadsUpConfig(HoldemConfig):
    name: str = "heads-up"
    max_players: int = 2
    starting_stack: float = 100.0


class HeadsUpEnvironment(HoldemEnvironment):
    """
    Heads-up poker environment.

    Optimized for 1v1 matches. Same as HoldemEnvironment
    but locked to 2 players with heads-up blind structure.
    """

    def __init__(self, **kwargs):
        config = HeadsUpConfig(**kwargs)
        super().__init__(config=config)

    def add_agent(self, agent) -> None:
        if len(self._agents) >= 2:
            raise ValueError("Heads-up environment only supports 2 agents")
        super().add_agent(agent)
