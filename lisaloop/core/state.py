"""
Game state representation — everything an agent needs to make a decision.

Usage:
    from lisaloop import GameState, Action, ActionType, Street

    state = game.get_state()
    state.my_hand          # Hand([A♠, K♥])
    state.board            # [T♠, 9♣, 2♦]
    state.pot              # 150.0
    state.street           # Street.FLOP
    state.my_stack         # 485.0
    state.valid_actions    # [Action(FOLD), Action(CALL, 50), Action(RAISE, 100, 485)]
    state.position         # 2 (0=SB, 1=BB, 2=UTG, ...)
    state.num_players      # 6
    state.history          # list of all actions this hand
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import Dict, List, Optional, Tuple

from lisaloop.core.cards import Card, Hand


class Street(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    SHOWDOWN = 4


class ActionType(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass(frozen=True)
class Action:
    """A poker action."""
    type: ActionType
    amount: float = 0.0
    min_raise: float = 0.0
    max_raise: float = 0.0

    @classmethod
    def fold(cls) -> Action:
        return cls(ActionType.FOLD)

    @classmethod
    def check(cls) -> Action:
        return cls(ActionType.CHECK)

    @classmethod
    def call(cls, amount: float) -> Action:
        return cls(ActionType.CALL, amount=amount)

    @classmethod
    def bet(cls, amount: float) -> Action:
        return cls(ActionType.BET, amount=amount)

    @classmethod
    def raise_to(cls, amount: float) -> Action:
        return cls(ActionType.RAISE, amount=amount)

    @classmethod
    def all_in(cls, amount: float) -> Action:
        return cls(ActionType.ALL_IN, amount=amount)

    def __repr__(self) -> str:
        if self.type in (ActionType.FOLD, ActionType.CHECK):
            return self.type.value.upper()
        return f"{self.type.value.upper()} ${self.amount:.2f}"


@dataclass
class ActionRecord:
    """A recorded action in hand history."""
    player_id: int
    player_name: str
    action: Action
    street: Street
    pot_after: float
    stack_after: float


@dataclass
class PlayerState:
    """Public information about a player at the table."""
    seat: int
    name: str
    stack: float
    bet: float = 0.0
    is_active: bool = True
    is_all_in: bool = False
    has_folded: bool = False
    is_dealer: bool = False
    is_sb: bool = False
    is_bb: bool = False

    @property
    def committed(self) -> float:
        return self.bet

    def __repr__(self) -> str:
        status = "active" if self.is_active and not self.has_folded else "folded" if self.has_folded else "all-in"
        pos = " [D]" if self.is_dealer else " [SB]" if self.is_sb else " [BB]" if self.is_bb else ""
        return f"{self.name}{pos} ${self.stack:.2f} ({status})"


@dataclass
class PotInfo:
    """Information about main pot and side pots."""
    main_pot: float = 0.0
    side_pots: List[Tuple[float, List[int]]] = field(default_factory=list)

    @property
    def total(self) -> float:
        return self.main_pot + sum(sp[0] for sp in self.side_pots)


@dataclass
class GameState:
    """
    Complete game state from the perspective of one player.
    This is the primary input to Agent.decide().
    """
    # My cards
    my_hand: Hand
    my_seat: int
    my_stack: float

    # Table state
    board: List[Card]
    street: Street
    pot: PotInfo
    players: List[PlayerState]
    dealer_seat: int

    # Action info
    valid_actions: List[Action]
    current_bet: float = 0.0
    min_raise: float = 0.0
    max_raise: float = 0.0

    # History
    history: List[ActionRecord] = field(default_factory=list)

    # Table metadata
    hand_number: int = 0
    table_id: str = ""
    small_blind: float = 0.25
    big_blind: float = 0.50

    @property
    def position(self) -> int:
        """Position relative to dealer (0=SB, 1=BB, 2=UTG, ...)"""
        active_seats = [p.seat for p in self.players if not p.has_folded]
        dealer_idx = active_seats.index(self.dealer_seat) if self.dealer_seat in active_seats else 0
        my_idx = active_seats.index(self.my_seat) if self.my_seat in active_seats else 0
        return (my_idx - dealer_idx - 1) % len(active_seats)

    @property
    def num_players(self) -> int:
        return len([p for p in self.players if not p.has_folded])

    @property
    def num_active(self) -> int:
        return len([p for p in self.players if p.is_active and not p.has_folded])

    @property
    def pot_odds(self) -> float:
        """Pot odds as a ratio. e.g., 0.33 means you need 33% equity to call."""
        call_amount = self.current_bet - self._my_player.bet
        if call_amount <= 0:
            return 0.0
        return call_amount / (self.pot.total + call_amount)

    @property
    def stack_to_pot_ratio(self) -> float:
        """SPR — effective stack / pot. Low SPR = committed."""
        if self.pot.total == 0:
            return float("inf")
        return self.my_stack / self.pot.total

    @property
    def is_heads_up(self) -> bool:
        return self.num_active == 2

    @property
    def street_history(self) -> List[ActionRecord]:
        """Actions on the current street only."""
        return [a for a in self.history if a.street == self.street]

    @property
    def _my_player(self) -> PlayerState:
        for p in self.players:
            if p.seat == self.my_seat:
                return p
        raise ValueError("Player not found")

    def can_check(self) -> bool:
        return any(a.type == ActionType.CHECK for a in self.valid_actions)

    def can_raise(self) -> bool:
        return any(a.type == ActionType.RAISE for a in self.valid_actions)

    def to_dict(self) -> Dict:
        """Serialize state for logging/analysis."""
        return {
            "hand": str(self.my_hand),
            "board": [str(c) for c in self.board],
            "street": self.street.name,
            "pot": self.pot.total,
            "stack": self.my_stack,
            "position": self.position,
            "num_players": self.num_players,
            "current_bet": self.current_bet,
            "hand_number": self.hand_number,
        }

    def __repr__(self) -> str:
        board_str = " ".join(repr(c) for c in self.board) if self.board else "—"
        return (
            f"Hand #{self.hand_number} | {self.street.name} | "
            f"Board: {board_str} | "
            f"Pot: ${self.pot.total:.2f} | "
            f"Hand: {self.my_hand!r} | "
            f"Stack: ${self.my_stack:.2f}"
        )
