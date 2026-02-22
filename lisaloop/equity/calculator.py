"""
Monte Carlo equity calculator.

Simulates thousands of runouts to estimate hand equity against
opponent ranges or specific holdings.

Usage:
    from lisaloop.equity import EquityCalculator

    calc = EquityCalculator()

    # Hand vs hand
    result = calc.evaluate("AhKh", "QsQd")
    print(f"AKs equity: {result.equities[0]:.1%}")

    # Hand vs range
    result = calc.evaluate("AhKh", "QQ+,AKs")
    print(f"AKs vs premium range: {result.equities[0]:.1%}")

    # Multi-way with board
    result = calc.evaluate("AhKh", "QsQd", board="Th9h2c", iterations=50000)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from itertools import combinations
from typing import List, Optional, Sequence, Tuple, Union

from lisaloop.core.cards import Card, Deck, Hand, HandEvaluator, Rank, Suit


@dataclass
class EquityResult:
    """Result from an equity calculation."""
    hands: List[str]
    equities: List[float]
    win_pcts: List[float]
    tie_pcts: List[float]
    iterations: int
    board: str

    def __repr__(self) -> str:
        lines = [f"Equity ({self.iterations:,} sims, board: {self.board or 'none'})"]
        for hand, eq, win, tie in zip(self.hands, self.equities, self.win_pcts, self.tie_pcts):
            lines.append(f"  {hand}: {eq:.1%} equity (win {win:.1%}, tie {tie:.1%})")
        return "\n".join(lines)


class EquityCalculator:
    """
    Monte Carlo equity calculator.

    Estimates hand equity by simulating random runouts and evaluating
    the resulting hands. Supports:
    - Hand vs hand (exact or Monte Carlo)
    - Hand vs range (see Range class)
    - Multi-way pots (up to 6 hands)
    - Partial boards (flop, turn, or preflop)
    """

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self._evaluator = HandEvaluator()

    def evaluate(
        self,
        *hands: str,
        board: str = "",
        iterations: int = 10000,
        dead: str = "",
    ) -> EquityResult:
        """
        Calculate equity for multiple hands.

        Args:
            *hands: Hand notations like "AhKh" or range strings like "QQ+,AKs"
            board: Community cards like "Th9h2c" (0, 3, 4, or 5 cards)
            iterations: Number of Monte Carlo simulations
            dead: Dead/mucked cards like "2c3d"

        Returns:
            EquityResult with equity percentages for each hand
        """
        if len(hands) < 2:
            raise ValueError("Need at least 2 hands to compare")

        board_cards = self._parse_cards(board) if board else []
        dead_cards = self._parse_cards(dead) if dead else []

        # Check if any hand is a range
        from lisaloop.equity.ranges import RangeParser
        parser = RangeParser()

        parsed_hands = []
        hand_labels = []
        for h in hands:
            if any(c in h for c in ["+", ",", "-"]) or len(h) <= 3:
                # This is a range notation
                range_obj = parser.parse(h)
                parsed_hands.append(("range", range_obj))
                hand_labels.append(h)
            else:
                parsed_hands.append(("hand", Hand.from_str(h)))
                hand_labels.append(h)

        wins = [0] * len(hands)
        ties = [0] * len(hands)
        total = 0

        for _ in range(iterations):
            # Build card pool (all cards not in board or dead)
            used = set(c.id for c in board_cards + dead_cards)

            # Resolve ranges to specific hands
            concrete_hands = []
            valid = True
            for kind, val in parsed_hands:
                if kind == "hand":
                    for c in val.cards:
                        if c.id in used:
                            valid = False
                            break
                        used.add(c.id)
                    concrete_hands.append(val)
                else:
                    # Pick a random hand from range that doesn't conflict
                    combos = val.get_combos()
                    self._rng.shuffle(combos)
                    found = False
                    for combo in combos:
                        h = Hand.from_str(combo)
                        if not any(c.id in used for c in h.cards):
                            for c in h.cards:
                                used.add(c.id)
                            concrete_hands.append(h)
                            found = True
                            break
                    if not found:
                        valid = False

                if not valid:
                    break

            if not valid:
                continue

            # Build remaining deck
            remaining = [
                Card(rank=rank, suit=suit)
                for suit in Suit for rank in Rank
                if (suit.value * 13 + (rank.value - 2)) not in used
            ]
            self._rng.shuffle(remaining)

            # Deal remaining board cards
            cards_needed = 5 - len(board_cards)
            sim_board = list(board_cards) + remaining[:cards_needed]

            # Evaluate all hands
            ranks = []
            for h in concrete_hands:
                rank = self._evaluator.evaluate(h, sim_board)
                ranks.append(rank)

            # Find winners
            best = max(ranks)
            winner_indices = [i for i, r in enumerate(ranks) if r == best]

            total += 1
            if len(winner_indices) == 1:
                wins[winner_indices[0]] += 1
            else:
                for i in winner_indices:
                    ties[i] += 1

        # Calculate percentages
        if total == 0:
            total = 1  # avoid div by zero

        equities = []
        win_pcts = []
        tie_pcts = []
        for w, t in zip(wins, ties):
            win_pct = w / total
            tie_pct = t / total
            equity = win_pct + tie_pct / 2
            equities.append(equity)
            win_pcts.append(win_pct)
            tie_pcts.append(tie_pct)

        return EquityResult(
            hands=hand_labels,
            equities=equities,
            win_pcts=win_pcts,
            tie_pcts=tie_pcts,
            iterations=total,
            board=board,
        )

    def _parse_cards(self, notation: str) -> List[Card]:
        """Parse a string of card notations like 'AhKh' or 'Th 9h 2c'."""
        notation = notation.replace(" ", "")
        cards = []
        for i in range(0, len(notation), 2):
            if i + 1 < len(notation):
                cards.append(Card(notation[i:i+2]))
        return cards
