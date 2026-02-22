"""
Card representation, deck management, and hand evaluation.

Usage:
    from lisaloop import Card, Hand, Deck, HandEvaluator

    card = Card("Ah")           # Ace of hearts
    hand = Hand([Card("Ah"), Card("Kh")])
    deck = Deck()
    deck.shuffle()
    flop = deck.deal(3)

    evaluator = HandEvaluator()
    rank = evaluator.evaluate(hand, flop)
    print(rank)  # HandRank(category=FLUSH, value=...)
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import IntEnum
from functools import total_ordering
from itertools import combinations
from typing import List, Optional, Sequence, Tuple


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    @property
    def symbol(self) -> str:
        return ["♣", "♦", "♥", "♠"][self.value]

    @property
    def letter(self) -> str:
        return ["c", "d", "h", "s"][self.value]


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def symbol(self) -> str:
        if self.value <= 9:
            return str(self.value)
        return {10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}[self.value]


RANK_MAP = {
    "2": Rank.TWO, "3": Rank.THREE, "4": Rank.FOUR, "5": Rank.FIVE,
    "6": Rank.SIX, "7": Rank.SEVEN, "8": Rank.EIGHT, "9": Rank.NINE,
    "T": Rank.TEN, "J": Rank.JACK, "Q": Rank.QUEEN, "K": Rank.KING, "A": Rank.ACE,
}

SUIT_MAP = {"c": Suit.CLUBS, "d": Suit.DIAMONDS, "h": Suit.HEARTS, "s": Suit.SPADES}


class HandCategory(IntEnum):
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9


@total_ordering
class Card:
    """A single playing card."""

    __slots__ = ("rank", "suit", "_id")

    def __init__(self, notation: str | None = None, *, rank: Rank | None = None, suit: Suit | None = None):
        if notation:
            if len(notation) != 2:
                raise ValueError(f"Invalid card notation: {notation!r}. Use format like 'Ah', 'Ts', '2c'.")
            r, s = notation[0].upper(), notation[1].lower()
            if r not in RANK_MAP:
                raise ValueError(f"Invalid rank: {r!r}")
            if s not in SUIT_MAP:
                raise ValueError(f"Invalid suit: {s!r}")
            self.rank = RANK_MAP[r]
            self.suit = SUIT_MAP[s]
        elif rank is not None and suit is not None:
            self.rank = rank
            self.suit = suit
        else:
            raise ValueError("Provide either notation string or rank+suit.")
        self._id = self.suit.value * 13 + (self.rank.value - 2)

    @property
    def id(self) -> int:
        return self._id

    def __repr__(self) -> str:
        return f"{self.rank.symbol}{self.suit.symbol}"

    def __str__(self) -> str:
        return f"{self.rank.symbol}{self.suit.letter}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self._id == other._id

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank < other.rank

    def __hash__(self) -> int:
        return self._id


class Hand:
    """A player's hole cards."""

    def __init__(self, cards: Sequence[Card]):
        if len(cards) != 2:
            raise ValueError("A hand must have exactly 2 cards.")
        self.cards = tuple(sorted(cards, reverse=True))

    @classmethod
    def from_str(cls, notation: str) -> Hand:
        """Parse 'AhKs' or 'Ah Ks' format."""
        notation = notation.replace(" ", "")
        if len(notation) != 4:
            raise ValueError(f"Invalid hand notation: {notation!r}")
        return cls([Card(notation[:2]), Card(notation[2:])])

    @property
    def is_pair(self) -> bool:
        return self.cards[0].rank == self.cards[1].rank

    @property
    def is_suited(self) -> bool:
        return self.cards[0].suit == self.cards[1].suit

    @property
    def gap(self) -> int:
        return abs(self.cards[0].rank - self.cards[1].rank)

    def __repr__(self) -> str:
        return f"[{self.cards[0]!r} {self.cards[1]!r}]"

    def __iter__(self):
        return iter(self.cards)

    def __contains__(self, card: Card) -> bool:
        return card in self.cards


class Deck:
    """A standard 52-card deck with shuffle and deal."""

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self._cards: List[Card] = []
        self._index = 0
        self.reset()

    def reset(self) -> None:
        self._cards = [
            Card(rank=rank, suit=suit)
            for suit in Suit
            for rank in Rank
        ]
        self._index = 0

    def shuffle(self) -> None:
        self._rng.shuffle(self._cards)
        self._index = 0

    def deal(self, n: int = 1) -> List[Card]:
        if self._index + n > len(self._cards):
            raise RuntimeError("Not enough cards in deck.")
        cards = self._cards[self._index:self._index + n]
        self._index += n
        return cards

    def deal_hand(self) -> Hand:
        return Hand(self.deal(2))

    def burn(self) -> None:
        self._index += 1

    def remove(self, cards: Sequence[Card]) -> None:
        card_ids = {c.id for c in cards}
        self._cards = [c for c in self._cards if c.id not in card_ids]

    @property
    def remaining(self) -> int:
        return len(self._cards) - self._index


@dataclass
class HandRank:
    """Result of hand evaluation."""
    category: HandCategory
    value: Tuple[int, ...]  # tiebreaker values, highest first
    best_five: Tuple[Card, ...]

    @property
    def name(self) -> str:
        return self.category.name.replace("_", " ").title()

    def __repr__(self) -> str:
        cards_str = " ".join(repr(c) for c in self.best_five)
        return f"{self.name} [{cards_str}]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HandRank):
            return NotImplemented
        return (self.category, self.value) == (other.category, other.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, HandRank):
            return NotImplemented
        return (self.category, self.value) < (other.category, other.value)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, HandRank):
            return NotImplemented
        return (self.category, self.value) <= (other.category, other.value)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, HandRank):
            return NotImplemented
        return (self.category, self.value) > (other.category, other.value)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, HandRank):
            return NotImplemented
        return (self.category, self.value) >= (other.category, other.value)


class HandEvaluator:
    """Evaluates the best 5-card hand from hole cards + community cards."""

    def evaluate(self, hand: Hand, board: Sequence[Card]) -> HandRank:
        all_cards = list(hand.cards) + list(board)
        if len(all_cards) < 5:
            raise ValueError(f"Need at least 5 cards, got {len(all_cards)}")

        best: Optional[HandRank] = None
        for combo in combinations(all_cards, 5):
            rank = self._evaluate_five(list(combo))
            if best is None or rank > best:
                best = rank
        return best  # type: ignore

    def _evaluate_five(self, cards: List[Card]) -> HandRank:
        cards_sorted = sorted(cards, key=lambda c: c.rank, reverse=True)
        ranks = [c.rank.value for c in cards_sorted]
        suits = [c.suit for c in cards_sorted]

        is_flush = len(set(suits)) == 1
        is_straight, straight_high = self._check_straight(ranks)

        rank_counts: dict[int, int] = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1

        counts_sorted = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

        if is_straight and is_flush:
            if straight_high == 14:
                return HandRank(HandCategory.ROYAL_FLUSH, (14,), tuple(cards_sorted))
            best_five = sorted(cards, key=lambda c: c.rank, reverse=True)
            if straight_high == 5:  # A-2-3-4-5
                best_five = self._sort_wheel(cards)
            return HandRank(HandCategory.STRAIGHT_FLUSH, (straight_high,), tuple(best_five))

        if counts_sorted[0][1] == 4:
            quad_rank = counts_sorted[0][0]
            kicker = counts_sorted[1][0]
            best = sorted([c for c in cards if c.rank.value == quad_rank], reverse=True)
            best += sorted([c for c in cards if c.rank.value == kicker], reverse=True)
            return HandRank(HandCategory.FOUR_OF_A_KIND, (quad_rank, kicker), tuple(best))

        if counts_sorted[0][1] == 3 and counts_sorted[1][1] == 2:
            trip_rank = counts_sorted[0][0]
            pair_rank = counts_sorted[1][0]
            best = sorted([c for c in cards if c.rank.value == trip_rank], reverse=True)
            best += sorted([c for c in cards if c.rank.value == pair_rank], reverse=True)
            return HandRank(HandCategory.FULL_HOUSE, (trip_rank, pair_rank), tuple(best))

        if is_flush:
            return HandRank(HandCategory.FLUSH, tuple(ranks), tuple(cards_sorted))

        if is_straight:
            best_five = cards_sorted
            if straight_high == 5:
                best_five = self._sort_wheel(cards)
            return HandRank(HandCategory.STRAIGHT, (straight_high,), tuple(best_five))

        if counts_sorted[0][1] == 3:
            trip_rank = counts_sorted[0][0]
            kickers = sorted([r for r, c in counts_sorted if c == 1], reverse=True)
            best = sorted([c for c in cards if c.rank.value == trip_rank], reverse=True)
            best += sorted([c for c in cards if c.rank.value in kickers], reverse=True)
            return HandRank(HandCategory.THREE_OF_A_KIND, (trip_rank, *kickers), tuple(best))

        if counts_sorted[0][1] == 2 and counts_sorted[1][1] == 2:
            high_pair = max(counts_sorted[0][0], counts_sorted[1][0])
            low_pair = min(counts_sorted[0][0], counts_sorted[1][0])
            kicker = [r for r, c in counts_sorted if c == 1][0]
            best = sorted([c for c in cards if c.rank.value == high_pair], reverse=True)
            best += sorted([c for c in cards if c.rank.value == low_pair], reverse=True)
            best += [c for c in cards if c.rank.value == kicker]
            return HandRank(HandCategory.TWO_PAIR, (high_pair, low_pair, kicker), tuple(best))

        if counts_sorted[0][1] == 2:
            pair_rank = counts_sorted[0][0]
            kickers = sorted([r for r, c in counts_sorted if c == 1], reverse=True)
            best = sorted([c for c in cards if c.rank.value == pair_rank], reverse=True)
            best += sorted([c for c in cards if c.rank.value in kickers], reverse=True)
            return HandRank(HandCategory.ONE_PAIR, (pair_rank, *kickers), tuple(best))

        return HandRank(HandCategory.HIGH_CARD, tuple(ranks), tuple(cards_sorted))

    @staticmethod
    def _check_straight(ranks: List[int]) -> Tuple[bool, int]:
        unique = sorted(set(ranks), reverse=True)
        if len(unique) < 5:
            return False, 0
        # Normal straight
        if unique[0] - unique[4] == 4:
            return True, unique[0]
        # Wheel: A-2-3-4-5
        if set(unique) == {14, 2, 3, 4, 5}:
            return True, 5
        return False, 0

    @staticmethod
    def _sort_wheel(cards: List[Card]) -> List[Card]:
        return sorted(cards, key=lambda c: 1 if c.rank == Rank.ACE else c.rank.value, reverse=True)
