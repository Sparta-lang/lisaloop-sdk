"""Random agent — picks a random valid action. Useful as a baseline."""

from __future__ import annotations

import random

from lisaloop.agents.base import Agent
from lisaloop.core.state import Action, ActionType, GameState


class RandomAgent(Agent):
    """Picks a random valid action with random sizing."""

    name = "RandomBot"
    description = "Chaotic neutral. Picks random actions with random sizing."

    def __init__(self, seed: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self._rng = random.Random(seed)

    def decide(self, state: GameState) -> Action:
        action = self._rng.choice(state.valid_actions)

        if action.type in (ActionType.RAISE, ActionType.BET) and action.max_raise > action.min_raise:
            amount = self._rng.uniform(action.min_raise, action.max_raise)
            if action.type == ActionType.RAISE:
                return Action.raise_to(amount)
            return Action.bet(amount)

        return action
