"""
Poker table simulation engine.

Runs full Texas Hold'em hands: deals cards, manages betting rounds,
evaluates winners, and distributes pots.

Usage:
    from lisaloop import Table, TableConfig

    table = Table(TableConfig(num_seats=6, small_blind=0.25, big_blind=0.50))
    table.seat_player(0, agent_a, name="Alice", stack=100.0)
    table.seat_player(1, agent_b, name="Bob", stack=100.0)
    result = table.play_hand()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from lisaloop.core.cards import Card, Deck, Hand, HandEvaluator
from lisaloop.core.state import (
    Action, ActionType, ActionRecord, GameState, PlayerState,
    PotInfo, Street,
)

if TYPE_CHECKING:
    from lisaloop.agents.base import Agent

logger = logging.getLogger("lisaloop.table")


@dataclass
class Blind:
    small: float = 0.25
    big: float = 0.50
    ante: float = 0.0


@dataclass
class TableConfig:
    num_seats: int = 6
    small_blind: float = 0.25
    big_blind: float = 0.50
    ante: float = 0.0
    min_buyin: float = 40.0
    max_buyin: float = 200.0
    seed: int | None = None


@dataclass
class SeatInfo:
    agent: Agent
    name: str
    stack: float
    hand: Optional[Hand] = None
    bet: float = 0.0
    total_bet: float = 0.0
    is_active: bool = True
    has_folded: bool = False
    is_all_in: bool = False
    winnings: float = 0.0


@dataclass
class HandResult:
    """Result of a single hand."""
    hand_number: int
    winners: Dict[int, float]  # seat -> amount won
    board: List[Card]
    showdown: Dict[int, Tuple[Hand, str]]  # seat -> (hand, rank_name)
    pot_total: float
    history: List[ActionRecord]
    duration_actions: int


class Table:
    """Full poker table simulation."""

    def __init__(self, config: TableConfig | None = None):
        self.config = config or TableConfig()
        self.seats: Dict[int, SeatInfo] = {}
        self.deck = Deck(seed=self.config.seed)
        self.evaluator = HandEvaluator()
        self.board: List[Card] = []
        self.pot = PotInfo()
        self.street = Street.PREFLOP
        self.dealer_seat = 0
        self.hand_number = 0
        self.history: List[ActionRecord] = []
        self._action_count = 0

    def seat_player(self, seat: int, agent: Agent, name: str = "", stack: float = 100.0) -> None:
        if seat < 0 or seat >= self.config.num_seats:
            raise ValueError(f"Seat {seat} out of range [0, {self.config.num_seats})")
        if seat in self.seats:
            raise ValueError(f"Seat {seat} is already taken by {self.seats[seat].name}")
        self.seats[seat] = SeatInfo(
            agent=agent,
            name=name or f"Player_{seat}",
            stack=stack,
        )

    def remove_player(self, seat: int) -> None:
        self.seats.pop(seat, None)

    @property
    def active_seats(self) -> List[int]:
        return sorted(s for s, info in self.seats.items() if info.stack > 0)

    def play_hand(self) -> HandResult:
        """Play a complete hand and return the result."""
        seats = self.active_seats
        if len(seats) < 2:
            raise RuntimeError("Need at least 2 players with chips.")

        self.hand_number += 1
        self._reset_hand()
        self._post_blinds()
        self._deal_hole_cards()

        # Betting rounds
        for street in [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER]:
            self.street = street
            if street != Street.PREFLOP:
                self._deal_community(street)

            if self._count_active() <= 1:
                break

            if self._count_can_act() >= 1:
                self._run_betting_round()

            if self._count_active() <= 1:
                break

        # Showdown / award pot
        result = self._resolve()

        # Advance dealer
        self._advance_dealer()

        return result

    def _reset_hand(self) -> None:
        self.deck.reset()
        self.deck.shuffle()
        self.board = []
        self.pot = PotInfo()
        self.street = Street.PREFLOP
        self.history = []
        self._action_count = 0

        for info in self.seats.values():
            info.hand = None
            info.bet = 0.0
            info.total_bet = 0.0
            info.is_active = info.stack > 0
            info.has_folded = False
            info.is_all_in = False
            info.winnings = 0.0

    def _post_blinds(self) -> None:
        seats = self.active_seats
        if len(seats) < 2:
            return

        dealer_idx = seats.index(self.dealer_seat) if self.dealer_seat in seats else 0

        if len(seats) == 2:
            sb_seat = seats[dealer_idx]
            bb_seat = seats[(dealer_idx + 1) % len(seats)]
        else:
            sb_seat = seats[(dealer_idx + 1) % len(seats)]
            bb_seat = seats[(dealer_idx + 2) % len(seats)]

        self._force_bet(sb_seat, min(self.config.small_blind, self.seats[sb_seat].stack))
        self._force_bet(bb_seat, min(self.config.big_blind, self.seats[bb_seat].stack))

        # Mark positions
        for s, info in self.seats.items():
            info_as_player = info
        self.seats[self.dealer_seat] if self.dealer_seat in self.seats else None

    def _force_bet(self, seat: int, amount: float) -> None:
        info = self.seats[seat]
        actual = min(amount, info.stack)
        info.bet += actual
        info.total_bet += actual
        info.stack -= actual
        self.pot.main_pot += actual
        if info.stack <= 0:
            info.is_all_in = True

    def _deal_hole_cards(self) -> None:
        for seat in self.active_seats:
            self.seats[seat].hand = self.deck.deal_hand()

    def _deal_community(self, street: Street) -> None:
        self.deck.burn()
        if street == Street.FLOP:
            self.board.extend(self.deck.deal(3))
        elif street in (Street.TURN, Street.RIVER):
            self.board.extend(self.deck.deal(1))

    def _run_betting_round(self) -> None:
        seats = self.active_seats
        current_bet = max((self.seats[s].bet for s in seats), default=0)

        if self.street == Street.PREFLOP:
            dealer_idx = seats.index(self.dealer_seat) if self.dealer_seat in seats else 0
            if len(seats) == 2:
                start_idx = dealer_idx
            else:
                start_idx = (dealer_idx + 3) % len(seats)
        else:
            dealer_idx = seats.index(self.dealer_seat) if self.dealer_seat in seats else 0
            start_idx = (dealer_idx + 1) % len(seats)

        last_raiser: Optional[int] = None
        idx = start_idx
        players_acted = 0
        min_raise = self.config.big_blind

        while True:
            seat = seats[idx]
            info = self.seats[seat]

            if not info.has_folded and not info.is_all_in and info.is_active:
                valid_actions = self._get_valid_actions(seat, current_bet, min_raise)
                state = self._build_state(seat, valid_actions, current_bet, min_raise)

                action = info.agent.decide(state)
                action = self._validate_action(action, valid_actions, seat, current_bet)

                self._apply_action(seat, action, current_bet)
                self._action_count += 1

                self.history.append(ActionRecord(
                    player_id=seat,
                    player_name=info.name,
                    action=action,
                    street=self.street,
                    pot_after=self.pot.total,
                    stack_after=info.stack,
                ))

                if action.type in (ActionType.RAISE, ActionType.BET, ActionType.ALL_IN):
                    if action.amount > current_bet:
                        raise_size = action.amount - current_bet
                        min_raise = max(min_raise, raise_size)
                        current_bet = action.amount
                        last_raiser = seat
                        players_acted = 1
                    else:
                        players_acted += 1
                else:
                    players_acted += 1
            else:
                players_acted += 1

            idx = (idx + 1) % len(seats)

            # Check if round is complete
            can_act = [s for s in seats if not self.seats[s].has_folded and not self.seats[s].is_all_in]
            if not can_act:
                break
            all_matched = all(self.seats[s].bet >= current_bet for s in can_act)
            if players_acted >= len(seats) and all_matched:
                break

        # Reset bets for next street
        for info in self.seats.values():
            info.bet = 0.0

    def _get_valid_actions(self, seat: int, current_bet: float, min_raise: float) -> List[Action]:
        info = self.seats[seat]
        actions: List[Action] = []
        to_call = current_bet - info.bet

        if to_call <= 0:
            actions.append(Action.check())
        else:
            actions.append(Action.fold())
            if to_call >= info.stack:
                actions.append(Action.all_in(info.stack + info.bet))
            else:
                actions.append(Action.call(to_call))

        # Raise/bet
        if to_call <= 0 and current_bet == 0:
            min_bet = self.config.big_blind
            if min_bet <= info.stack:
                max_bet = info.stack
                actions.append(Action(ActionType.BET, amount=min_bet, min_raise=min_bet, max_raise=max_bet))
        elif info.stack > to_call:
            raise_min = current_bet + min_raise
            raise_max = info.stack + info.bet
            if raise_min <= raise_max:
                actions.append(Action(ActionType.RAISE, amount=raise_min, min_raise=raise_min, max_raise=raise_max))

        # All-in is always an option if you have chips
        if info.stack > 0 and not any(a.type == ActionType.ALL_IN for a in actions):
            actions.append(Action.all_in(info.stack + info.bet))

        return actions

    def _validate_action(self, action: Action, valid: List[Action], seat: int, current_bet: float) -> Action:
        valid_types = {a.type for a in valid}

        if action.type not in valid_types:
            # Default: check if possible, else fold
            if ActionType.CHECK in valid_types:
                return Action.check()
            return Action.fold()

        if action.type == ActionType.RAISE:
            raise_action = next((a for a in valid if a.type == ActionType.RAISE), None)
            if raise_action:
                clamped = max(raise_action.min_raise, min(action.amount, raise_action.max_raise))
                return Action.raise_to(clamped)

        if action.type == ActionType.BET:
            bet_action = next((a for a in valid if a.type == ActionType.BET), None)
            if bet_action:
                clamped = max(bet_action.min_raise, min(action.amount, bet_action.max_raise))
                return Action.bet(clamped)

        return action

    def _apply_action(self, seat: int, action: Action, current_bet: float) -> None:
        info = self.seats[seat]

        if action.type == ActionType.FOLD:
            info.has_folded = True
            info.is_active = False

        elif action.type == ActionType.CHECK:
            pass

        elif action.type == ActionType.CALL:
            actual = min(action.amount, info.stack)
            info.stack -= actual
            info.bet += actual
            info.total_bet += actual
            self.pot.main_pot += actual
            if info.stack <= 0:
                info.is_all_in = True

        elif action.type in (ActionType.BET, ActionType.RAISE):
            needed = action.amount - info.bet
            actual = min(needed, info.stack)
            info.stack -= actual
            info.bet += actual
            info.total_bet += actual
            self.pot.main_pot += actual
            if info.stack <= 0:
                info.is_all_in = True

        elif action.type == ActionType.ALL_IN:
            actual = info.stack
            info.stack = 0
            info.bet += actual
            info.total_bet += actual
            self.pot.main_pot += actual
            info.is_all_in = True

    def _build_state(self, seat: int, valid_actions: List[Action], current_bet: float, min_raise: float) -> GameState:
        info = self.seats[seat]
        players = []
        for s in sorted(self.seats.keys()):
            si = self.seats[s]
            players.append(PlayerState(
                seat=s,
                name=si.name,
                stack=si.stack,
                bet=si.bet,
                is_active=si.is_active,
                is_all_in=si.is_all_in,
                has_folded=si.has_folded,
                is_dealer=(s == self.dealer_seat),
            ))

        return GameState(
            my_hand=info.hand,  # type: ignore
            my_seat=seat,
            my_stack=info.stack,
            board=list(self.board),
            street=self.street,
            pot=PotInfo(main_pot=self.pot.main_pot, side_pots=list(self.pot.side_pots)),
            players=players,
            dealer_seat=self.dealer_seat,
            valid_actions=valid_actions,
            current_bet=current_bet,
            min_raise=min_raise,
            max_raise=info.stack + info.bet,
            history=list(self.history),
            hand_number=self.hand_number,
            small_blind=self.config.small_blind,
            big_blind=self.config.big_blind,
        )

    def _resolve(self) -> HandResult:
        active = [(s, info) for s, info in self.seats.items() if not info.has_folded and info.hand]
        showdown: Dict[int, Tuple[Hand, str]] = {}
        winners: Dict[int, float] = {}

        if len(active) == 1:
            winner_seat, winner_info = active[0]
            winner_info.winnings = self.pot.total
            winner_info.stack += self.pot.total
            winners[winner_seat] = self.pot.total
        else:
            # Evaluate hands
            rankings = []
            for seat, info in active:
                rank = self.evaluator.evaluate(info.hand, self.board)  # type: ignore
                rankings.append((seat, info, rank))
                showdown[seat] = (info.hand, rank.name)  # type: ignore

            rankings.sort(key=lambda x: x[2], reverse=True)

            # Find best rank
            best_rank = rankings[0][2]
            hand_winners = [(s, info) for s, info, r in rankings if r == best_rank]

            share = self.pot.total / len(hand_winners)
            for seat, info in hand_winners:
                info.winnings = share
                info.stack += share
                winners[seat] = share

        return HandResult(
            hand_number=self.hand_number,
            winners=winners,
            board=list(self.board),
            showdown=showdown,
            pot_total=self.pot.total,
            history=list(self.history),
            duration_actions=self._action_count,
        )

    def _count_active(self) -> int:
        return len([s for s, info in self.seats.items() if not info.has_folded])

    def _count_can_act(self) -> int:
        return len([s for s, info in self.seats.items() if not info.has_folded and not info.is_all_in and info.stack > 0])

    def _advance_dealer(self) -> None:
        seats = self.active_seats
        if not seats:
            return
        if self.dealer_seat in seats:
            idx = seats.index(self.dealer_seat)
            self.dealer_seat = seats[(idx + 1) % len(seats)]
        else:
            self.dealer_seat = seats[0]
