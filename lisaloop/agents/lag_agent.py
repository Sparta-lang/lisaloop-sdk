"""Loose-Aggressive (LAG) agent — plays many hands, applies constant pressure."""

from __future__ import annotations

import random

from lisaloop.agents.base import Agent
from lisaloop.core.state import Action, ActionType, GameState, Street


class LAGAgent(Agent):
    """
    Loose-Aggressive: plays ~35% of hands, raises frequently,
    bluffs often, applies maximum pressure. High variance.
    """

    name = "LAGBot"
    description = "Loose-aggressive. Plays wide, raises often, bluffs frequently. VPIP ~35%, PFR ~28%."

    def __init__(self, bluff_freq: float = 0.35, seed: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self._bluff_freq = bluff_freq
        self._rng = random.Random(seed)

    def decide(self, state: GameState) -> Action:
        if state.street == Street.PREFLOP:
            return self._preflop(state)
        return self._postflop(state)

    def _preflop(self, state: GameState) -> Action:
        r1 = state.my_hand.cards[0].rank.value
        r2 = state.my_hand.cards[1].rank.value
        high = max(r1, r2)
        is_suited = state.my_hand.is_suited
        is_pair = state.my_hand.is_pair
        gap = abs(r1 - r2)

        # Play ~35% of hands
        should_play = (
            is_pair
            or high >= 12
            or (high >= 10 and min(r1, r2) >= 8)
            or (is_suited and gap <= 3 and high >= 6)
            or (is_suited and high >= 11)
            or self._rng.random() < 0.08  # random bluff opens
        )

        if not should_play:
            if state.can_check():
                return Action.check()
            return Action.fold()

        # Raise most hands we play
        if self._rng.random() < 0.8:
            raise_action = next((a for a in state.valid_actions if a.type in (ActionType.RAISE, ActionType.BET)), None)
            if raise_action:
                size = min(state.big_blind * self._rng.uniform(2.2, 3.5), raise_action.max_raise)
                return Action.raise_to(size) if raise_action.type == ActionType.RAISE else Action.bet(size)

        return Action.call(state.current_bet) if state.current_bet > 0 else Action.check()

    def _postflop(self, state: GameState) -> Action:
        has_hand = self._has_equity(state)

        # Bet/raise with hands OR as bluffs
        should_aggress = has_hand or self._rng.random() < self._bluff_freq

        if should_aggress:
            if state.can_check():
                bet_action = next((a for a in state.valid_actions if a.type == ActionType.BET), None)
                if bet_action:
                    # Vary bet sizing
                    pot_frac = self._rng.uniform(0.5, 1.0)
                    size = min(state.pot.total * pot_frac, bet_action.max_raise)
                    return Action.bet(max(size, bet_action.min_raise))
            elif state.can_raise() and self._rng.random() < 0.4:
                raise_action = next((a for a in state.valid_actions if a.type == ActionType.RAISE), None)
                if raise_action:
                    size = min(state.current_bet * self._rng.uniform(2.0, 3.0), raise_action.max_raise)
                    return Action.raise_to(max(size, raise_action.min_raise))
            elif has_hand:
                return Action.call(state.current_bet)

        if state.can_check():
            return Action.check()

        # Call with some equity, fold without
        if has_hand and state.pot_odds < 0.4:
            return Action.call(state.current_bet)

        return Action.fold()

    def _has_equity(self, state: GameState) -> bool:
        if not state.board:
            return True
        my_ranks = {c.rank for c in state.my_hand.cards}
        my_suits = {c.suit for c in state.my_hand.cards}
        board_ranks = {c.rank for c in state.board}
        board_suits = [c.suit for c in state.board]

        # Pair+
        if my_ranks & board_ranks:
            return True
        # Overpair
        if state.my_hand.is_pair and state.my_hand.cards[0].rank > max(c.rank for c in state.board):
            return True
        # Flush draw
        for suit in my_suits:
            if board_suits.count(suit) + 1 >= 4:
                return True
        # Straight draw (rough)
        all_ranks = sorted(set(list(my_ranks) + list(board_ranks)))
        for i in range(len(all_ranks) - 3):
            if all_ranks[i + 3] - all_ranks[i] <= 4:
                return True
        # High cards
        if max(c.rank.value for c in state.my_hand.cards) >= 12:
            return True
        return False
