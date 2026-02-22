"""GTO Approximation agent — mixed strategy based on simplified game theory."""

from __future__ import annotations

import random
from collections import defaultdict

from lisaloop.agents.base import Agent
from lisaloop.core.cards import HandEvaluator, Rank
from lisaloop.core.state import Action, ActionType, GameState, Street


class GTOApproxAgent(Agent):
    """
    Approximates GTO play using mixed strategies.
    Balances value bets and bluffs at theoretically sound ratios.
    Uses pot geometry and minimum defense frequency.
    """

    name = "GTOBot"
    version = "1.0"
    description = "GTO approximation. Mixed strategies, balanced ranges, pot-geometric sizing."

    def __init__(self, seed: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self._rng = random.Random(seed)
        self._evaluator = HandEvaluator()

    def decide(self, state: GameState) -> Action:
        if state.street == Street.PREFLOP:
            return self._preflop(state)
        return self._postflop(state)

    def _preflop(self, state: GameState) -> Action:
        strength = self._preflop_strength(state)

        # Open-raise range (~22% of hands)
        if state.current_bet <= state.big_blind:
            if strength >= 0.78:
                raise_action = next((a for a in state.valid_actions if a.type in (ActionType.RAISE, ActionType.BET)), None)
                if raise_action:
                    size = min(state.big_blind * 2.5, raise_action.max_raise)
                    return Action.raise_to(size) if raise_action.type == ActionType.RAISE else Action.bet(size)
            if state.can_check():
                return Action.check()
            return Action.fold()

        # Facing a raise
        if strength >= 0.92:  # 3-bet range (~8%)
            raise_action = next((a for a in state.valid_actions if a.type == ActionType.RAISE), None)
            if raise_action:
                size = min(state.current_bet * 3, raise_action.max_raise)
                return Action.raise_to(size)
        if strength >= 0.78:  # Call range
            return Action.call(state.current_bet)

        # Fold
        if state.can_check():
            return Action.check()
        return Action.fold()

    def _postflop(self, state: GameState) -> Action:
        hand_strength = self._postflop_strength(state)

        # Pot-geometric bet sizing: size bets to get all-in by river
        streets_left = max(1, 3 - state.street.value)
        geometric_size = self._geometric_bet_size(state.pot.total, state.my_stack, streets_left)

        # Value threshold: bet with top ~60% of continuing range
        # Bluff threshold: bluff with ~33% of bets (2:1 value-to-bluff)
        value_threshold = 0.6
        bluff_threshold = 0.2

        is_value = hand_strength >= value_threshold
        is_bluff = hand_strength < bluff_threshold and self._has_draw(state)

        if state.can_check():
            if is_value or (is_bluff and self._rng.random() < 0.33):
                bet_action = next((a for a in state.valid_actions if a.type == ActionType.BET), None)
                if bet_action:
                    size = max(geometric_size, bet_action.min_raise)
                    size = min(size, bet_action.max_raise)
                    return Action.bet(size)
            return Action.check()

        # Facing a bet — use minimum defense frequency
        mdf = 1.0 - state.pot_odds  # minimum defense frequency
        defend_threshold = 1.0 - mdf

        if hand_strength >= defend_threshold:
            # Sometimes raise for value
            if hand_strength >= 0.85 and self._rng.random() < 0.25 and state.can_raise():
                raise_action = next((a for a in state.valid_actions if a.type == ActionType.RAISE), None)
                if raise_action:
                    size = min(state.current_bet * 2.5, raise_action.max_raise)
                    return Action.raise_to(max(size, raise_action.min_raise))
            return Action.call(state.current_bet)

        # Bluff raise sometimes
        if is_bluff and self._rng.random() < 0.15 and state.can_raise():
            raise_action = next((a for a in state.valid_actions if a.type == ActionType.RAISE), None)
            if raise_action:
                size = min(state.current_bet * 2.5, raise_action.max_raise)
                return Action.raise_to(max(size, raise_action.min_raise))

        return Action.fold()

    def _preflop_strength(self, state: GameState) -> float:
        """Returns 0.0-1.0 representing preflop hand strength percentile."""
        r1 = state.my_hand.cards[0].rank.value
        r2 = state.my_hand.cards[1].rank.value
        high, low = max(r1, r2), min(r1, r2)
        is_pair = high == low
        is_suited = state.my_hand.is_suited

        score = 0.0

        if is_pair:
            score = 0.5 + (high - 2) * 0.04  # 22=0.5, AA=0.98
        else:
            score = (high + low - 4) / 24  # raw card strength
            if is_suited:
                score += 0.04
            gap = high - low
            if gap <= 1:
                score += 0.03
            elif gap >= 4:
                score -= 0.03

        return max(0.0, min(1.0, score))

    def _postflop_strength(self, state: GameState) -> float:
        """Estimate hand strength vs random opponent hand."""
        if not state.board:
            return self._preflop_strength(state)

        my_ranks = [c.rank.value for c in state.my_hand.cards]
        board_ranks = [c.rank.value for c in state.board]
        high_card = max(my_ranks)

        strength = 0.3  # baseline

        # Pair
        for r in my_ranks:
            if r in board_ranks:
                strength += 0.25
                if r == max(board_ranks):
                    strength += 0.1  # top pair
                break

        # Overpair
        if state.my_hand.is_pair and state.my_hand.cards[0].rank.value > max(board_ranks):
            strength += 0.35

        # Two pair or better (rough)
        matches = sum(1 for r in my_ranks if r in board_ranks)
        if matches == 2:
            strength += 0.4

        # Flush/straight draws add equity
        if self._has_flush_draw(state):
            strength += 0.15
        if self._has_straight_draw(state):
            strength += 0.1

        # High card kicker
        strength += (high_card - 8) * 0.02

        return max(0.0, min(1.0, strength))

    def _geometric_bet_size(self, pot: float, stack: float, streets_left: int) -> float:
        """Calculate bet size to geometrically grow pot to stack size by river."""
        if streets_left <= 0 or pot <= 0:
            return pot * 0.66
        # Solve: pot * (1 + 2x)^n = pot + stack → x = ((pot+stack)/pot)^(1/n) - 1) / 2
        target = pot + stack
        ratio = target / pot
        per_street_growth = ratio ** (1 / streets_left)
        bet_fraction = (per_street_growth - 1) / 2
        return pot * min(bet_fraction, 1.0)

    def _has_draw(self, state: GameState) -> bool:
        return self._has_flush_draw(state) or self._has_straight_draw(state)

    def _has_flush_draw(self, state: GameState) -> bool:
        if len(state.board) < 3:
            return False
        suits = defaultdict(int)
        for c in list(state.my_hand.cards) + state.board:
            suits[c.suit] += 1
        return any(v >= 4 for v in suits.values())

    def _has_straight_draw(self, state: GameState) -> bool:
        if len(state.board) < 3:
            return False
        all_ranks = sorted(set(c.rank.value for c in list(state.my_hand.cards) + state.board))
        for i in range(len(all_ranks)):
            window = [r for r in all_ranks if all_ranks[i] <= r <= all_ranks[i] + 4]
            if len(window) >= 4:
                return True
        return False
