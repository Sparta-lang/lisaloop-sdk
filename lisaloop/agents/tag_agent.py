"""Tight-Aggressive (TAG) agent — plays few hands, plays them hard."""

from __future__ import annotations

import random

from lisaloop.agents.base import Agent
from lisaloop.core.cards import Rank
from lisaloop.core.state import Action, ActionType, GameState, Street


# Simplified hand strength tiers (preflop)
PREMIUM = {(14, 14), (13, 13), (12, 12), (14, 13)}  # AA, KK, QQ, AK
STRONG = {(11, 11), (10, 10), (14, 12), (14, 11), (13, 12)}  # JJ, TT, AQ, AJ, KQ
PLAYABLE = {(9, 9), (8, 8), (14, 10), (13, 11), (12, 11), (11, 10)}  # 99-88, AT, KJ, QJ, JT


def _hand_tier(state: GameState) -> int:
    """Returns 0=premium, 1=strong, 2=playable, 3=trash."""
    r1 = state.my_hand.cards[0].rank.value
    r2 = state.my_hand.cards[1].rank.value
    key = (max(r1, r2), min(r1, r2))

    if key in PREMIUM:
        return 0
    if key in STRONG:
        return 1
    if key in PLAYABLE:
        return 2
    # Suited connectors
    if state.my_hand.is_suited and abs(r1 - r2) == 1 and min(r1, r2) >= 7:
        return 2
    # Pocket pairs
    if r1 == r2 and r1 >= 6:
        return 2
    return 3


class TAGAgent(Agent):
    """
    Tight-Aggressive: plays ~20% of hands, raises with strong holdings,
    c-bets most flops, shuts down on scary boards without a hand.
    """

    name = "TAGBot"
    description = "Tight-aggressive. Plays few hands, plays them hard. VPIP ~20%, PFR ~16%."

    def __init__(self, aggression: float = 0.7, seed: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self._aggression = aggression
        self._rng = random.Random(seed)
        self._raised_preflop = False

    def on_hand_start(self, hand_number: int, my_stack: float) -> None:
        self._raised_preflop = False

    def decide(self, state: GameState) -> Action:
        if state.street == Street.PREFLOP:
            return self._preflop(state)
        return self._postflop(state)

    def _preflop(self, state: GameState) -> Action:
        tier = _hand_tier(state)

        # Premium: always raise/3-bet
        if tier == 0:
            self._raised_preflop = True
            if state.can_raise():
                raise_action = next((a for a in state.valid_actions if a.type == ActionType.RAISE), None)
                if raise_action:
                    size = min(state.current_bet * 3 + state.big_blind, raise_action.max_raise)
                    return Action.raise_to(size)
            return Action.call(state.current_bet)

        # Strong: raise if no raise yet, call a raise
        if tier == 1:
            if state.current_bet <= state.big_blind:
                self._raised_preflop = True
                raise_action = next((a for a in state.valid_actions if a.type in (ActionType.RAISE, ActionType.BET)), None)
                if raise_action:
                    size = min(state.big_blind * 3, raise_action.max_raise)
                    return Action.raise_to(size) if raise_action.type == ActionType.RAISE else Action.bet(size)
            if state.current_bet <= state.big_blind * 4:
                return Action.call(state.current_bet)
            return Action.fold()

        # Playable: open-raise or call small raises in position
        if tier == 2:
            if state.current_bet <= state.big_blind and state.position >= state.num_players // 2:
                self._raised_preflop = True
                raise_action = next((a for a in state.valid_actions if a.type in (ActionType.RAISE, ActionType.BET)), None)
                if raise_action:
                    size = min(state.big_blind * 2.5, raise_action.max_raise)
                    return Action.raise_to(size) if raise_action.type == ActionType.RAISE else Action.bet(size)
            if state.current_bet <= state.big_blind * 3 and state.position >= state.num_players - 2:
                return Action.call(state.current_bet)
            if state.can_check():
                return Action.check()
            return Action.fold()

        # Trash: fold (or check if free)
        if state.can_check():
            return Action.check()
        return Action.fold()

    def _postflop(self, state: GameState) -> Action:
        # Simple postflop: c-bet if we raised preflop, otherwise play fit-or-fold
        has_pair_or_better = self._has_made_hand(state)

        # C-bet on flop if we were the preflop aggressor
        if state.street == Street.FLOP and self._raised_preflop and state.can_check():
            if self._rng.random() < self._aggression:
                bet_action = next((a for a in state.valid_actions if a.type == ActionType.BET), None)
                if bet_action:
                    size = min(state.pot.total * 0.66, bet_action.max_raise)
                    return Action.bet(max(size, bet_action.min_raise))

        # With a made hand, bet/raise
        if has_pair_or_better:
            if state.can_check():
                bet_action = next((a for a in state.valid_actions if a.type == ActionType.BET), None)
                if bet_action and self._rng.random() < self._aggression:
                    size = min(state.pot.total * 0.6, bet_action.max_raise)
                    return Action.bet(max(size, bet_action.min_raise))
                return Action.check()
            else:
                # Facing a bet with a hand — call or raise
                if self._rng.random() < 0.3 and state.can_raise():
                    raise_action = next((a for a in state.valid_actions if a.type == ActionType.RAISE), None)
                    if raise_action:
                        size = min(state.current_bet * 2.5, raise_action.max_raise)
                        return Action.raise_to(max(size, raise_action.min_raise))
                return Action.call(state.current_bet)

        # No hand — check or fold
        if state.can_check():
            return Action.check()
        return Action.fold()

    def _has_made_hand(self, state: GameState) -> bool:
        """Quick check if we have at least a pair with the board."""
        if not state.board:
            return False
        my_ranks = {c.rank for c in state.my_hand.cards}
        board_ranks = {c.rank for c in state.board}
        # Pair or overpair
        if my_ranks & board_ranks:
            return True
        # Overpair
        if state.my_hand.is_pair and state.my_hand.cards[0].rank > max(c.rank for c in state.board):
            return True
        return False
