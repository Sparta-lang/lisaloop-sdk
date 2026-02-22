"""
ConfigurableAgent — an agent driven by a Character definition.

Instead of hardcoding strategy in Python, this agent reads its
behavior from a Character config. Change the JSON file,
change the agent's personality.

Usage:
    from lisaloop.config import Character
    char = Character(name="Duffman", aggression=0.9, tightness=0.85)
    agent = char.to_agent(seed=42)
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from lisaloop.agents.base import Agent
from lisaloop.core.state import Action, ActionType, GameState, Street

if TYPE_CHECKING:
    from lisaloop.config.character import Character


class ConfigurableAgent(Agent):
    """
    An agent whose behavior is defined by a Character config file.

    All strategy parameters (aggression, tightness, bluff frequency,
    c-bet frequency, etc.) come from the Character definition.
    """

    def __init__(self, character: Character, seed: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self.character = character
        self.name = character.name
        self.version = character.version
        self.author = character.author
        self.description = character.description
        self._rng = random.Random(seed)

    def decide(self, state: GameState) -> Action:
        if state.street == Street.PREFLOP:
            return self._preflop(state)
        return self._postflop(state)

    def _preflop(self, state: GameState) -> Action:
        strength = self._hand_strength(state)
        c = self.character

        # Tightness determines the threshold for opening
        open_threshold = c.tightness

        # Position bonus
        pos_bonus = (state.position / max(1, state.num_players)) * c.position_awareness * 0.15
        adjusted = strength + pos_bonus

        # Open-raise
        if state.current_bet <= state.big_blind:
            if adjusted >= open_threshold:
                raise_action = next(
                    (a for a in state.valid_actions if a.type in (ActionType.RAISE, ActionType.BET)), None
                )
                if raise_action:
                    size = state.big_blind * (2.0 + c.aggression)
                    size = max(raise_action.min_raise, min(size, raise_action.max_raise))
                    return Action.raise_to(size) if raise_action.type == ActionType.RAISE else Action.bet(size)
            if state.can_check():
                return Action.check()
            return Action.fold()

        # Facing a raise
        if adjusted >= 0.90:
            raise_action = next((a for a in state.valid_actions if a.type == ActionType.RAISE), None)
            if raise_action:
                size = state.current_bet * (2.5 + c.aggression)
                size = max(raise_action.min_raise, min(size, raise_action.max_raise))
                return Action.raise_to(size)
        if adjusted >= open_threshold - 0.05:
            return Action.call(state.current_bet)

        if state.can_check():
            return Action.check()
        return Action.fold()

    def _postflop(self, state: GameState) -> Action:
        strength = self._hand_strength(state)
        c = self.character

        if state.can_check():
            # C-bet
            if state.street == Street.FLOP and self._rng.random() < c.cbet_frequency:
                if strength >= 0.4 or self._rng.random() < c.bluff_frequency:
                    return self._make_bet(state, 0.5 + c.aggression * 0.2)

            # Value bet strong hands
            if strength >= 0.7:
                return self._make_bet(state, 0.5 + c.aggression * 0.3)

            # Bluff
            if self._rng.random() < c.bluff_frequency:
                return self._make_bet(state, 0.33 + c.aggression * 0.15)

            return Action.check()

        # Facing a bet
        if strength >= 0.8:
            if self._rng.random() < c.aggression * 0.4 and state.can_raise():
                return self._make_raise(state, 2.5)
            return Action.call(state.current_bet)

        if strength >= (1.0 - (1.0 - state.pot_odds)):
            return Action.call(state.current_bet)

        # Check-raise bluff
        if self._rng.random() < c.check_raise_frequency and state.can_raise():
            return self._make_raise(state, 3.0)

        return Action.fold()

    def _make_bet(self, state: GameState, pot_fraction: float) -> Action:
        bet_action = next((a for a in state.valid_actions if a.type == ActionType.BET), None)
        if not bet_action:
            return Action.check()
        size = state.pot.total * pot_fraction
        size = max(bet_action.min_raise, min(size, bet_action.max_raise))
        return Action.bet(size)

    def _make_raise(self, state: GameState, multiplier: float) -> Action:
        raise_action = next((a for a in state.valid_actions if a.type == ActionType.RAISE), None)
        if not raise_action:
            return Action.call(state.current_bet)
        size = state.current_bet * multiplier
        size = max(raise_action.min_raise, min(size, raise_action.max_raise))
        return Action.raise_to(size)

    def _hand_strength(self, state: GameState) -> float:
        r1 = state.my_hand.cards[0].rank.value
        r2 = state.my_hand.cards[1].rank.value
        high, low = max(r1, r2), min(r1, r2)

        if high == low:
            score = 0.5 + (high - 2) * 0.04
        else:
            score = (high + low - 4) / 24
            if state.my_hand.is_suited:
                score += 0.05
            gap = high - low
            if gap <= 1:
                score += 0.04
            elif gap >= 4:
                score -= 0.04

        if state.board:
            board_ranks = [c.rank.value for c in state.board]
            my_ranks = [c.rank.value for c in state.my_hand.cards]
            for r in my_ranks:
                if r in board_ranks:
                    score += 0.25
                    break

        return max(0.0, min(1.0, score))
