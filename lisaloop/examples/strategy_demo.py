"""
Strategy Tools Demo — Sizing, position charts, and ICM.

Shows how to use Lisa's built-in strategy tools for
bet sizing, preflop decisions, and tournament calculations.
"""

from lisaloop.core.state import Street
from lisaloop.strategy import BetSizer, SizingContext, PositionCharts, ICMCalculator


def main():
    # ── Bet Sizing ──────────────────────────────────
    print("\n  ── Bet Sizing Engine ──")
    print("  " + "─" * 50)

    sizer = BetSizer()

    ctx = SizingContext(pot=100, stack=500, street=Street.FLOP, streets_remaining=3)
    geo = sizer.geometric(ctx)
    value = sizer.value_size(ctx, hand_strength=0.85)
    bluff = sizer.bluff_size(ctx)

    print(f"  Pot: $100 | Stack: $500 | Street: Flop")
    print(f"    Geometric size:  ${geo:.2f} (sets up all-in by river)")
    print(f"    Value size (85%): ${value:.2f}")
    print(f"    Bluff size:      ${bluff:.2f}")

    # River spot
    ctx_river = SizingContext(pot=300, stack=200, street=Street.RIVER, streets_remaining=0)
    overbet = sizer.overbet(ctx_river, multiplier=1.5)
    print(f"\n  River: Pot $300, Stack $200")
    print(f"    Overbet (1.5x):  ${overbet:.2f}")

    # 3-bet sizing
    three_bet = sizer.three_bet_size(open_raise=6.0, in_position=True)
    four_bet = sizer.four_bet_size(three_bet)
    print(f"\n  Open raise: $6.00")
    print(f"    3-bet IP:  ${three_bet:.2f}")
    print(f"    4-bet:     ${four_bet:.2f}")

    # ── Position Charts ──────────────────────────────
    print("\n\n  ── Position Charts ──")
    print("  " + "─" * 50)

    charts = PositionCharts()

    # Check specific hands
    hands_to_check = ["AKs", "QQ", "T9s", "87o", "A5s", "KJo"]
    positions = ["UTG", "CO", "BTN"]

    print(f"\n  {'Hand':<8}", end="")
    for pos in positions:
        print(f"{pos:>8}", end="")
    print()
    print("  " + "─" * 32)

    for hand in hands_to_check:
        print(f"  {hand:<8}", end="")
        for pos in positions:
            opens = charts.should_open(pos, hand)
            print(f"{'OPEN':>8}" if opens else f"{'fold':>8}", end="")
        print()

    # Display BTN chart
    charts.display("BTN")

    # ── ICM Calculator ───────────────────────────────
    print("\n  ── ICM Calculator ──")
    print("  " + "─" * 50)

    icm = ICMCalculator()

    # 3-player SNG with 50/30/20 payouts
    stacks = [5000, 3000, 2000]
    payouts = [50, 30, 20]

    equities = icm.calculate(stacks, payouts)
    print(f"\n  Stacks: {stacks}")
    print(f"  Payouts: {payouts}%")
    print(f"\n  ICM Equity:")
    for i, (stack, eq) in enumerate(zip(stacks, equities)):
        chip_pct = stack / sum(stacks) * 100
        print(f"    Player {i+1}: {stack} chips ({chip_pct:.0f}%) → {eq:.1f}% equity")

    # Decision EV
    print(f"\n  Should Player 1 call an all-in from Player 3?")
    ev = icm.decision_ev(
        stacks=stacks,
        payouts=payouts,
        hero=0,
        win_stacks=[7000, 3000, 0],
        lose_stacks=[3000, 3000, 4000],
        win_prob=0.60,
    )
    print(f"    Win prob: 60% | ICM EV: {ev:+.2f}%")
    print(f"    Decision: {'CALL' if ev > 0 else 'FOLD'}")

    # Bubble factor
    bf = icm.bubble_factor(stacks, payouts, hero=0, villain=2, pot=2000)
    print(f"\n  Bubble factor (P1 vs P3, pot=2000): {bf:.2f}x")
    print(f"    Need {50 * bf:.0f}% equity instead of 50% (chip EV)")

    print()


if __name__ == "__main__":
    main()
