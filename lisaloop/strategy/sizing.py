"""
Bet sizing engine with pot-geometric and exploitative sizing.

Usage:
    from lisaloop.strategy import BetSizer, SizingContext

    sizer = BetSizer()
    ctx = SizingContext(pot=100, stack=500, street=Street.FLOP, streets_remaining=3)
    size = sizer.geometric(ctx)         # Pot-geometric size to get all-in by river
    size = sizer.value_size(ctx, 0.8)   # Value sizing for strong hand
    size = sizer.bluff_size(ctx)        # Bluff sizing (minimize risk)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from lisaloop.core.state import Street


@dataclass
class SizingContext:
    """Context for sizing calculations."""
    pot: float
    stack: float
    street: Street = Street.FLOP
    streets_remaining: int = 3
    num_opponents: int = 1
    opponent_stack: float = 0.0
    in_position: bool = True


class BetSizer:
    """
    Strategic bet sizing calculator.

    Implements multiple sizing strategies:
    - Pot-geometric: Bet to set up a natural all-in by river
    - Value sizing: Extract maximum from calling ranges
    - Bluff sizing: Minimize risk while maintaining fold equity
    - Overbet: Put maximum pressure on capped ranges
    """

    def geometric(self, ctx: SizingContext) -> float:
        """
        Pot-geometric sizing.

        Calculates the bet size that, if used on each remaining street,
        naturally results in an all-in by the river.

        This is the theoretically optimal sizing for polarized ranges.
        """
        if ctx.streets_remaining <= 0:
            return min(ctx.pot, ctx.stack)

        # Solve: pot * (1 + 2x)^n = pot + 2*stack
        # Where x = fraction of pot to bet, n = streets remaining
        # Simplified: x = ((pot + 2*stack) / pot)^(1/n) - 1) / 2
        target = ctx.pot + 2 * ctx.stack
        ratio = target / max(0.01, ctx.pot)

        if ratio <= 1:
            return 0

        fraction = (ratio ** (1 / ctx.streets_remaining) - 1) / 2
        size = ctx.pot * fraction
        return max(0, min(size, ctx.stack))

    def value_size(self, ctx: SizingContext, hand_strength: float) -> float:
        """
        Value sizing based on hand strength.

        Stronger hands size larger to extract maximum value.
        Weaker value hands size smaller to keep worse hands calling.

        Args:
            hand_strength: 0.0 to 1.0 (0=air, 1=nuts)
        """
        # Map strength to pot fraction
        if hand_strength >= 0.9:
            # Nuts-level: go big, sometimes overbet
            fraction = 0.75 + (hand_strength - 0.9) * 2.5
        elif hand_strength >= 0.7:
            # Strong value: standard sizing
            fraction = 0.55 + (hand_strength - 0.7) * 1.0
        elif hand_strength >= 0.5:
            # Medium value: smaller to keep bluff-catchers calling
            fraction = 0.33 + (hand_strength - 0.5) * 1.1
        else:
            # Weak: tiny or check
            fraction = 0.25

        # Adjust for position
        if not ctx.in_position:
            fraction *= 0.9  # Size down slightly OOP

        # Adjust for multiway
        if ctx.num_opponents > 1:
            fraction *= 0.85  # Size down in multiway pots

        size = ctx.pot * fraction
        return max(0, min(size, ctx.stack))

    def bluff_size(self, ctx: SizingContext) -> float:
        """
        Bluff sizing — minimize risk while maintaining fold equity.

        Uses smaller sizings (25-40% pot) to get good bluff odds.
        On later streets, sizes up slightly to increase pressure.
        """
        street_factor = {
            Street.FLOP: 0.33,
            Street.TURN: 0.40,
            Street.RIVER: 0.50,
        }.get(ctx.street, 0.33)

        size = ctx.pot * street_factor
        return max(0, min(size, ctx.stack))

    def overbet(self, ctx: SizingContext, multiplier: float = 1.5) -> float:
        """
        Overbet sizing for polarized spots.

        Used when opponent's range is capped (can't have strong hands)
        and you have a polarized range (nuts or air).

        Args:
            multiplier: Pot multiplier (default 1.5x pot)
        """
        size = ctx.pot * multiplier
        return max(0, min(size, ctx.stack))

    def three_bet_size(self, open_raise: float, in_position: bool = True) -> float:
        """
        Standard 3-bet sizing.

        In position: 3x the open raise
        Out of position: 3.5-4x the open raise (to discourage flatting)
        """
        if in_position:
            return open_raise * 3.0
        return open_raise * 3.75

    def four_bet_size(self, three_bet: float) -> float:
        """Standard 4-bet sizing: 2.25x the 3-bet."""
        return three_bet * 2.25
