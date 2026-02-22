"""
Lisa Agent — the flagship agent. Combines neural heuristics with
adaptive opponent modeling. This is the agent that grinds on PokerStars.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, List

from lisaloop.agents.base import Agent
from lisaloop.core.cards import HandEvaluator
from lisaloop.core.state import Action, ActionType, GameState, Street


class OpponentModel:
    """Tracks opponent tendencies over time."""

    def __init__(self):
        self.hands_seen = 0
        self.vpip = 0  # voluntarily put $ in pot
        self.pfr = 0   # preflop raise
        self.af_bets = 0  # aggression: bets + raises
        self.af_calls = 0  # aggression: calls
        self.cbet = 0
        self.cbet_opportunities = 0
        self.fold_to_cbet = 0
        self.fold_to_cbet_opportunities = 0
        self.three_bet = 0
        self.three_bet_opportunities = 0

    @property
    def vpip_pct(self) -> float:
        return self.vpip / max(1, self.hands_seen)

    @property
    def pfr_pct(self) -> float:
        return self.pfr / max(1, self.hands_seen)

    @property
    def aggression_factor(self) -> float:
        return self.af_bets / max(1, self.af_calls)

    @property
    def cbet_pct(self) -> float:
        return self.cbet / max(1, self.cbet_opportunities)

    @property
    def fold_to_cbet_pct(self) -> float:
        return self.fold_to_cbet / max(1, self.fold_to_cbet_opportunities)

    @property
    def is_fish(self) -> bool:
        return self.hands_seen >= 20 and self.vpip_pct > 0.40

    @property
    def is_nit(self) -> bool:
        return self.hands_seen >= 20 and self.vpip_pct < 0.15

    @property
    def is_lag(self) -> bool:
        return self.hands_seen >= 20 and self.vpip_pct > 0.28 and self.aggression_factor > 2.0

    def summary(self) -> str:
        if self.hands_seen < 10:
            return "unknown"
        if self.is_fish:
            return "fish"
        if self.is_nit:
            return "nit"
        if self.is_lag:
            return "LAG"
        return "TAG"


class LisaAgent(Agent):
    """
    Lisa Loop's core agent. Adaptive, exploitative play.

    Combines:
    - Preflop hand charts adjusted by position and opponent tendencies
    - Postflop play based on hand strength + pot geometry
    - Opponent modeling to shift between exploitative and balanced play
    - Dynamic bluff frequency based on board texture
    """

    name = "Lisa"
    version = "0.8"
    author = "Lisa Loop"
    description = "Adaptive exploitative agent with opponent modeling. The one that grinds."

    def __init__(self, seed: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self._rng = random.Random(seed)
        self._evaluator = HandEvaluator()
        self._opponents: Dict[str, OpponentModel] = defaultdict(OpponentModel)
        self._was_preflop_aggressor = False

    def on_hand_start(self, hand_number: int, my_stack: float) -> None:
        self._was_preflop_aggressor = False

    def on_opponent_action(self, player_name: str, action: Action, street: int) -> None:
        model = self._opponents[player_name]
        if street == Street.PREFLOP:
            if action.type in (ActionType.CALL, ActionType.RAISE, ActionType.BET, ActionType.ALL_IN):
                model.vpip += 1
            if action.type in (ActionType.RAISE, ActionType.BET):
                model.pfr += 1
        if action.type in (ActionType.BET, ActionType.RAISE):
            model.af_bets += 1
        elif action.type == ActionType.CALL:
            model.af_calls += 1

    def decide(self, state: GameState) -> Action:
        if state.street == Street.PREFLOP:
            return self._preflop(state)
        return self._postflop(state)

    def _preflop(self, state: GameState) -> Action:
        strength = self._hand_strength_preflop(state)
        position_bonus = state.position / max(1, state.num_players) * 0.1
        adjusted = strength + position_bonus

        # Identify opponent types for adjustments
        villain_models = self._get_active_opponent_models(state)
        fish_at_table = any(m.is_fish for m in villain_models)
        nits_at_table = all(m.is_nit for m in villain_models) if villain_models else False

        # Widen range vs fish, tighten vs nits
        open_threshold = 0.68
        if fish_at_table:
            open_threshold -= 0.08
        if nits_at_table:
            open_threshold += 0.05

        # Open-raise
        if state.current_bet <= state.big_blind:
            if adjusted >= open_threshold:
                self._was_preflop_aggressor = True
                raise_action = next((a for a in state.valid_actions if a.type in (ActionType.RAISE, ActionType.BET)), None)
                if raise_action:
                    size = min(state.big_blind * 2.5, raise_action.max_raise)
                    return Action.raise_to(size) if raise_action.type == ActionType.RAISE else Action.bet(size)
            if state.can_check():
                return Action.check()
            return Action.fold()

        # Facing a raise
        if adjusted >= 0.90:
            self._was_preflop_aggressor = True
            raise_action = next((a for a in state.valid_actions if a.type == ActionType.RAISE), None)
            if raise_action:
                size = min(state.current_bet * 3, raise_action.max_raise)
                return Action.raise_to(size)
        if adjusted >= open_threshold:
            return Action.call(state.current_bet)

        if state.can_check():
            return Action.check()
        return Action.fold()

    def _postflop(self, state: GameState) -> Action:
        strength = self._hand_strength_postflop(state)
        has_draw = self._has_draw(state)
        board_texture = self._board_texture(state)
        villain_models = self._get_active_opponent_models(state)

        # Adjust bluff frequency based on board and opponents
        base_bluff_freq = 0.30
        if board_texture == "dry":
            base_bluff_freq = 0.35  # bluff more on dry boards
        elif board_texture == "wet":
            base_bluff_freq = 0.20  # less bluffing on draw-heavy boards

        if any(m.is_fish for m in villain_models):
            base_bluff_freq *= 0.5  # don't bluff fish

        # --- In position, no bet to us ---
        if state.can_check():
            # C-bet if preflop aggressor
            if self._was_preflop_aggressor and state.street == Street.FLOP:
                cbet_freq = 0.65
                if any(m.fold_to_cbet_pct > 0.6 for m in villain_models):
                    cbet_freq = 0.80  # exploit high fold-to-cbet
                if strength >= 0.5 or (has_draw and self._rng.random() < cbet_freq):
                    return self._make_bet(state, 0.55)
                if self._rng.random() < base_bluff_freq:
                    return self._make_bet(state, 0.55)

            # Value bet with strong hands
            if strength >= 0.7:
                return self._make_bet(state, 0.6 + self._rng.uniform(-0.1, 0.15))

            # Semi-bluff with draws
            if has_draw and self._rng.random() < base_bluff_freq:
                return self._make_bet(state, 0.5)

            return Action.check()

        # --- Facing a bet ---
        mdf = 1.0 - state.pot_odds

        if strength >= 0.85:
            # Strong hand — raise sometimes
            if self._rng.random() < 0.3 and state.can_raise():
                return self._make_raise(state, 2.5)
            return Action.call(state.current_bet)

        if strength >= (1.0 - mdf):
            # Medium hand — call
            return Action.call(state.current_bet)

        # Draw — call if pot odds are good
        if has_draw and state.pot_odds < 0.30:
            return Action.call(state.current_bet)

        # Bluff raise
        if has_draw and self._rng.random() < 0.12 and state.can_raise():
            return self._make_raise(state, 2.8)

        return Action.fold()

    def _make_bet(self, state: GameState, pot_fraction: float) -> Action:
        bet_action = next((a for a in state.valid_actions if a.type == ActionType.BET), None)
        if not bet_action:
            return Action.check()
        size = state.pot.total * pot_fraction
        size = max(size, bet_action.min_raise)
        size = min(size, bet_action.max_raise)
        return Action.bet(size)

    def _make_raise(self, state: GameState, multiplier: float) -> Action:
        raise_action = next((a for a in state.valid_actions if a.type == ActionType.RAISE), None)
        if not raise_action:
            return Action.call(state.current_bet)
        size = state.current_bet * multiplier
        size = max(size, raise_action.min_raise)
        size = min(size, raise_action.max_raise)
        return Action.raise_to(size)

    def _hand_strength_preflop(self, state: GameState) -> float:
        r1 = state.my_hand.cards[0].rank.value
        r2 = state.my_hand.cards[1].rank.value
        high, low = max(r1, r2), min(r1, r2)

        if high == low:
            return 0.5 + (high - 2) * 0.04
        score = (high + low - 4) / 24
        if state.my_hand.is_suited:
            score += 0.05
        gap = high - low
        if gap <= 1:
            score += 0.04
        elif gap >= 4:
            score -= 0.04
        return max(0.0, min(1.0, score))

    def _hand_strength_postflop(self, state: GameState) -> float:
        if not state.board:
            return self._hand_strength_preflop(state)

        strength = 0.25
        my_ranks = [c.rank.value for c in state.my_hand.cards]
        board_ranks = [c.rank.value for c in state.board]

        # Pair
        for r in my_ranks:
            if r in board_ranks:
                strength += 0.25
                if r == max(board_ranks):
                    strength += 0.1
                if r >= 12:
                    strength += 0.05
                break

        # Overpair
        if state.my_hand.is_pair and state.my_hand.cards[0].rank.value > max(board_ranks):
            strength += 0.35

        # Two pair
        if sum(1 for r in my_ranks if r in board_ranks) == 2:
            strength += 0.4

        # Flush draw adds equity
        if self._has_flush_draw(state):
            strength += 0.15

        # Straight draw
        if self._has_straight_draw(state):
            strength += 0.10

        # High card
        strength += (max(my_ranks) - 8) * 0.015

        return max(0.0, min(1.0, strength))

    def _board_texture(self, state: GameState) -> str:
        if len(state.board) < 3:
            return "unknown"
        suits = defaultdict(int)
        for c in state.board:
            suits[c.suit] += 1
        ranks = sorted(c.rank.value for c in state.board)

        is_monotone = max(suits.values()) >= 3
        is_connected = (ranks[-1] - ranks[0]) <= 4
        has_pairs = len(set(ranks)) < len(ranks)

        if is_monotone or is_connected:
            return "wet"
        if has_pairs:
            return "paired"
        return "dry"

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

    def _get_active_opponent_models(self, state: GameState) -> List[OpponentModel]:
        models = []
        for p in state.players:
            if p.seat != state.my_seat and not p.has_folded:
                models.append(self._opponents[p.name])
        return models
