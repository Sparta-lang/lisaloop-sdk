"""
Hand range notation parser and manipulation.

Supports standard poker range notation:
    "AA"           → All combos of pocket aces
    "AKs"          → Ace-King suited
    "AKo"          → Ace-King offsuit
    "AK"           → Both suited and offsuit
    "QQ+"          → QQ, KK, AA
    "TT-88"        → TT, 99, 88
    "ATs+"         → ATs, AJs, AQs, AKs
    "QQ+,AKs,AKo"  → Combined ranges

Usage:
    from lisaloop.equity import Range, RangeParser

    parser = RangeParser()
    r = parser.parse("QQ+,AKs,JTs+")
    print(r.combos)       # List of specific combos
    print(r.pct_of_hands) # What % of all hands this covers
    print(r)              # Pretty grid display
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set, Tuple

from lisaloop.core.cards import Rank, Suit

RANK_ORDER = "23456789TJQKA"
RANK_CHARS = list(RANK_ORDER)


def _rank_idx(ch: str) -> int:
    return RANK_CHARS.index(ch.upper())


@dataclass
class Range:
    """A set of poker hand combos."""
    _combos: Set[str] = field(default_factory=set)

    @property
    def combos(self) -> List[str]:
        return sorted(self._combos)

    @property
    def num_combos(self) -> int:
        return len(self._combos)

    @property
    def pct_of_hands(self) -> float:
        """What percentage of all 1326 starting hands this range covers."""
        return len(self._combos) / 1326 * 100

    def contains(self, hand: str) -> bool:
        """Check if a specific combo is in this range."""
        hand = hand.replace(" ", "")
        return hand in self._combos or hand[::-1] in self._combos

    def get_combos(self) -> List[str]:
        """Get all combos as 4-char notations like 'AhKs'."""
        return list(self._combos)

    def add(self, other: Range) -> Range:
        """Combine two ranges."""
        combined = Range()
        combined._combos = self._combos | other._combos
        return combined

    def remove(self, other: Range) -> Range:
        """Remove hands from this range."""
        result = Range()
        result._combos = self._combos - other._combos
        return result

    def __len__(self) -> int:
        return len(self._combos)

    def __repr__(self) -> str:
        return f"Range({len(self._combos)} combos, {self.pct_of_hands:.1f}% of hands)"

    def grid(self) -> str:
        """Display as a 13x13 grid showing which hand classes are in the range."""
        lines = []
        header = "    " + "  ".join(f" {r}" for r in reversed(RANK_CHARS))
        lines.append(header)

        for i, r1 in enumerate(reversed(RANK_CHARS)):
            row = f" {r1}  "
            for j, r2 in enumerate(reversed(RANK_CHARS)):
                real_i = 12 - i  # index in RANK_CHARS
                real_j = 12 - j
                if real_i == real_j:
                    label = f"{r1}{r2}"
                    count = self._count_pair(r1)
                    total = 6
                elif real_i > real_j:
                    label = f"{r1}{r2}s"
                    count = self._count_suited(r1, r2)
                    total = 4
                else:
                    label = f"{r2}{r1}o"
                    count = self._count_offsuit(r2, r1)
                    total = 12

                if count == total:
                    row += " ## "
                elif count > 0:
                    row += " .. "
                else:
                    row += " -- "
            lines.append(row)

        lines.append("")
        lines.append("  ## = all combos  .. = some combos  -- = not in range")
        return "\n".join(lines)

    def _count_pair(self, rank_ch: str) -> int:
        rank = RANK_CHARS.index(rank_ch) + 2
        count = 0
        suits = [s.letter for s in Suit]
        for i, s1 in enumerate(suits):
            for s2 in suits[i+1:]:
                combo = f"{rank_ch}{s1}{rank_ch}{s2}"
                if combo in self._combos:
                    count += 1
        return count

    def _count_suited(self, r1_ch: str, r2_ch: str) -> int:
        count = 0
        for s in Suit:
            combo = f"{r1_ch}{s.letter}{r2_ch}{s.letter}"
            if combo in self._combos:
                count += 1
        return count

    def _count_offsuit(self, r1_ch: str, r2_ch: str) -> int:
        count = 0
        for s1 in Suit:
            for s2 in Suit:
                if s1 != s2:
                    combo = f"{r1_ch}{s1.letter}{r2_ch}{s2.letter}"
                    if combo in self._combos:
                        count += 1
        return count


class RangeParser:
    """Parses standard poker range notation into Range objects."""

    def parse(self, notation: str) -> Range:
        """
        Parse range notation.

        Examples:
            "AA"           → 6 combos of pocket aces
            "AKs"          → 4 combos of AK suited
            "AKo"          → 12 combos of AK offsuit
            "QQ+"          → QQ through AA (18 combos)
            "TT-88"        → TT, 99, 88 (18 combos)
            "ATs+"         → ATs through AKs (16 combos)
            "QQ+,AKs,ATs+" → Combined range
        """
        result = Range()
        parts = [p.strip() for p in notation.split(",")]

        for part in parts:
            if not part:
                continue
            combos = self._parse_part(part)
            result._combos |= combos

        return result

    def _parse_part(self, part: str) -> Set[str]:
        """Parse a single range component."""
        part = part.strip()

        # Dash range: TT-88 or ATs-A8s
        if "-" in part:
            return self._parse_dash_range(part)

        # Plus range: QQ+ or ATs+
        if part.endswith("+"):
            return self._parse_plus_range(part[:-1])

        # Single hand class: AA, AKs, AKo, AK
        return self._expand_hand_class(part)

    def _parse_plus_range(self, base: str) -> Set[str]:
        """Parse QQ+ or ATs+ notation."""
        combos = set()

        if len(base) == 2 and base[0] == base[1]:
            # Pair+: QQ+ means QQ, KK, AA
            start_idx = _rank_idx(base[0])
            for i in range(start_idx, 13):
                r = RANK_CHARS[i]
                combos |= self._expand_hand_class(f"{r}{r}")
        elif len(base) == 3 and base[2] in ("s", "o"):
            # Suited/offsuit+: ATs+ means ATs, AJs, AQs, AKs
            high_idx = _rank_idx(base[0])
            start_idx = _rank_idx(base[1])
            suffix = base[2]
            for i in range(start_idx, high_idx):
                r = RANK_CHARS[i]
                combos |= self._expand_hand_class(f"{base[0]}{r}{suffix}")
        elif len(base) == 2:
            # Both suited and offsuit: AT+ means ATs+, ATo+
            high_idx = _rank_idx(base[0])
            start_idx = _rank_idx(base[1])
            for i in range(start_idx, high_idx):
                r = RANK_CHARS[i]
                combos |= self._expand_hand_class(f"{base[0]}{r}")

        return combos

    def _parse_dash_range(self, notation: str) -> Set[str]:
        """Parse TT-88 or ATs-A8s notation."""
        parts = notation.split("-")
        if len(parts) != 2:
            return set()

        start, end = parts[0].strip(), parts[1].strip()
        combos = set()

        # Pair range: TT-88
        if len(start) == 2 and start[0] == start[1] and len(end) == 2 and end[0] == end[1]:
            lo = min(_rank_idx(start[0]), _rank_idx(end[0]))
            hi = max(_rank_idx(start[0]), _rank_idx(end[0]))
            for i in range(lo, hi + 1):
                r = RANK_CHARS[i]
                combos |= self._expand_hand_class(f"{r}{r}")
        # Suited range: ATs-A8s
        elif len(start) >= 2 and len(end) >= 2:
            suffix = ""
            if len(start) == 3:
                suffix = start[2]
            high = start[0]
            lo = min(_rank_idx(start[1]), _rank_idx(end[1]))
            hi = max(_rank_idx(start[1]), _rank_idx(end[1]))
            for i in range(lo, hi + 1):
                r = RANK_CHARS[i]
                combos |= self._expand_hand_class(f"{high}{r}{suffix}")

        return combos

    def _expand_hand_class(self, notation: str) -> Set[str]:
        """Expand a hand class to all specific combos."""
        combos = set()

        if len(notation) == 2:
            r1, r2 = notation[0], notation[1]
            if r1 == r2:
                # Pair: all 6 combos
                suits = [s.letter for s in Suit]
                for i, s1 in enumerate(suits):
                    for s2 in suits[i+1:]:
                        combos.add(f"{r1}{s1}{r2}{s2}")
            else:
                # Both suited and offsuit
                for s1 in Suit:
                    for s2 in Suit:
                        if s1 == s2:
                            combos.add(f"{r1}{s1.letter}{r2}{s2.letter}")
                        else:
                            combos.add(f"{r1}{s1.letter}{r2}{s2.letter}")

        elif len(notation) == 3:
            r1, r2, stype = notation[0], notation[1], notation[2]
            if stype == "s":
                # Suited: 4 combos
                for s in Suit:
                    combos.add(f"{r1}{s.letter}{r2}{s.letter}")
            elif stype == "o":
                # Offsuit: 12 combos
                for s1 in Suit:
                    for s2 in Suit:
                        if s1 != s2:
                            combos.add(f"{r1}{s1.letter}{r2}{s2.letter}")

        return combos
