"""
Game environment abstraction — run agents in different game formats.

The base environment defines the contract that all game types implement.
This makes it easy to swap between cash games, tournaments, heads-up,
and eventually non-poker games.

Usage:
    from lisaloop.environments import HoldemEnvironment

    env = HoldemEnvironment(seats=6, blinds=(0.25, 0.50))
    env.add_agent(LisaAgent())
    env.add_agent(TAGAgent())

    # Run N hands
    results = env.run(hands=1000)

    # Step through one hand at a time
    env.reset()
    result = env.step()
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from lisaloop.agents.base import Agent


@dataclass
class EnvConfig:
    """Base configuration for any game environment."""
    name: str = "base"
    max_players: int = 6
    seed: int | None = None


class GameEnvironment(ABC):
    """
    Abstract base for all game environments.

    Defines the contract:
    - add_agent() / remove_agent()
    - reset() — prepare for a new game/hand
    - step() — advance one hand/round
    - run(n) — run N steps
    - get_state() — current environment state
    """

    def __init__(self, config: EnvConfig | None = None):
        self.config = config or EnvConfig()
        self._agents: List[Agent] = []

    @abstractmethod
    def reset(self) -> None:
        """Reset the environment for a new game/hand."""
        ...

    @abstractmethod
    def step(self) -> Any:
        """Advance one step (one hand in poker). Returns result."""
        ...

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get current environment state."""
        ...

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the environment."""
        if len(self._agents) >= self.config.max_players:
            raise ValueError(f"Environment full ({self.config.max_players} max)")
        self._agents.append(agent)

    def remove_agent(self, name: str) -> None:
        """Remove an agent by name."""
        self._agents = [a for a in self._agents if a.name != name]

    def run(self, hands: int = 100) -> List[Any]:
        """Run multiple hands and return all results."""
        self.reset()
        results = []
        for _ in range(hands):
            result = self.step()
            if result:
                results.append(result)
        return results

    @property
    def agents(self) -> List[Agent]:
        return list(self._agents)

    @property
    def num_agents(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.num_agents} agents)"
