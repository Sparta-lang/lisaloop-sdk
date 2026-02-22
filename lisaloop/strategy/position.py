"""
Position-based opening charts and ranges.

Pre-computed opening ranges for each position at 6-max tables,
based on GTO approximations.

Usage:
    from lisaloop.strategy import PositionCharts

    charts = PositionCharts()
    hands = charts.open_range("UTG")        # Get opening range
    should_open = charts.should_open("UTG", "ATs")  # Check specific hand
    charts.display("CO")                     # Print visual chart
"""

from __future__ import annotations

from typing import Dict, List, Set


# Standard 6-max opening ranges (GTO approximation)
# Format: {position: [hand classes]}
OPENING_RANGES: Dict[str, Set[str]] = {
    "UTG": {
        # ~15% of hands
        "AA", "KK", "QQ", "JJ", "TT", "99", "88",
        "AKs", "AQs", "AJs", "ATs",
        "AKo", "AQo",
        "KQs", "KJs",
        "QJs",
    },
    "HJ": {
        # ~19% of hands
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A5s", "A4s",
        "AKo", "AQo", "AJo",
        "KQs", "KJs", "KTs",
        "QJs", "QTs",
        "JTs",
    },
    "CO": {
        # ~27% of hands
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
        "AKo", "AQo", "AJo", "ATo",
        "KQs", "KJs", "KTs", "K9s",
        "KQo",
        "QJs", "QTs", "Q9s",
        "JTs", "J9s",
        "T9s",
        "98s",
        "87s",
        "76s",
    },
    "BTN": {
        # ~40% of hands
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
        "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o",
        "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s",
        "KQo", "KJo", "KTo",
        "QJs", "QTs", "Q9s", "Q8s",
        "QJo", "QTo",
        "JTs", "J9s", "J8s",
        "JTo",
        "T9s", "T8s",
        "98s", "97s",
        "87s", "86s",
        "76s", "75s",
        "65s", "64s",
        "54s",
    },
    "SB": {
        # ~36% of hands (tighter than BTN because OOP post)
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
        "AKo", "AQo", "AJo", "ATo", "A9o",
        "KQs", "KJs", "KTs", "K9s", "K8s",
        "KQo", "KJo",
        "QJs", "QTs", "Q9s",
        "QJo",
        "JTs", "J9s",
        "T9s", "T8s",
        "98s", "97s",
        "87s",
        "76s",
        "65s",
        "54s",
    },
    "BB": {
        # BB defends wide vs opens — this is the 3-bet range
        "AA", "KK", "QQ", "JJ", "TT",
        "AKs", "AQs", "AJs",
        "AKo",
        "KQs",
        # Also has a wide call range (not listed — that's position dependent)
    },
}

POSITION_ORDER = ["UTG", "HJ", "CO", "BTN", "SB", "BB"]
RANK_ORDER = "AKQJT98765432"


class PositionCharts:
    """
    GTO-approximation opening charts for 6-max.

    Includes opening ranges for each position, visual grid display,
    and hand-checking utilities.
    """

    def __init__(self):
        self._ranges = OPENING_RANGES

    def open_range(self, position: str) -> Set[str]:
        """Get the opening range for a position."""
        pos = position.upper()
        if pos not in self._ranges:
            raise ValueError(f"Unknown position: {pos}. Use: {', '.join(POSITION_ORDER)}")
        return self._ranges[pos]

    def should_open(self, position: str, hand: str) -> bool:
        """
        Check if a hand should be opened from this position.

        Args:
            position: "UTG", "HJ", "CO", "BTN", "SB", or "BB"
            hand: Hand class notation like "AKs", "QQ", "T9o"
        """
        range_set = self.open_range(position)
        hand = hand.strip()

        # Direct match
        if hand in range_set:
            return True

        # Check if it's a pair (e.g., "AA" or "TT")
        if len(hand) == 2 and hand[0] == hand[1]:
            return hand in range_set

        # Normalize to high-low format
        if len(hand) == 2:
            r1, r2 = hand[0], hand[1]
            i1, i2 = RANK_ORDER.index(r1), RANK_ORDER.index(r2)
            if i1 > i2:
                hand = f"{r2}{r1}"
            # Check both suited and offsuit
            return f"{hand}s" in range_set or f"{hand}o" in range_set or hand in range_set

        if len(hand) == 3:
            r1, r2, stype = hand[0], hand[1], hand[2]
            i1, i2 = RANK_ORDER.index(r1), RANK_ORDER.index(r2)
            if i1 > i2:
                hand = f"{r2}{r1}{stype}"
            return hand in range_set

        return False

    def display(self, position: str) -> str:
        """Display opening chart as a visual grid."""
        range_set = self.open_range(position)

        lines = []
        lines.append(f"\n  {position} Opening Range ({len(range_set)} hand classes)")
        lines.append(f"  {'─' * 56}")
        lines.append("")

        header = "       " + "  ".join(f"{r:>2}" for r in RANK_ORDER)
        lines.append(header)

        for i, r1 in enumerate(RANK_ORDER):
            row = f"    {r1}  "
            for j, r2 in enumerate(RANK_ORDER):
                if i == j:
                    hand = f"{r1}{r2}"
                elif i < j:
                    hand = f"{r1}{r2}s"
                else:
                    hand = f"{r2}{r1}o"

                if hand in range_set:
                    row += " ██"
                else:
                    row += "  ·"

            lines.append(row)

        lines.append("")
        lines.append("  ██ = open    · = fold")
        lines.append(f"  Rows = suited (below diagonal), Offsuit (above)")
        lines.append("")

        text = "\n".join(lines)
        print(text)
        return text

    def all_positions(self) -> str:
        """Display summary of all position ranges."""
        lines = ["\n  6-Max Opening Ranges Summary", f"  {'═' * 40}", ""]
        for pos in POSITION_ORDER:
            count = len(self._ranges[pos])
            lines.append(f"  {pos:>4}: {count:>3} hand classes")
        lines.append("")
        return "\n".join(lines)
