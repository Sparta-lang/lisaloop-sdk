"""
Equity Calculator Demo — Monte Carlo equity estimation.

Shows how to use the equity calculator for hand vs hand,
hand vs range, and multi-way equity calculations.
"""

from lisaloop.equity import EquityCalculator, Range, RangeParser

def main():
    calc = EquityCalculator(seed=42)

    # ── Hand vs Hand ──────────────────────────────────
    print("\n  ── Hand vs Hand ──")
    print("  " + "─" * 40)

    result = calc.evaluate("AhKh", "QsQd", iterations=20000)
    print(f"  AKs vs QQ:")
    print(f"    AKs:  {result.equities[0]:.1%} equity")
    print(f"    QQ:   {result.equities[1]:.1%} equity")

    # ── With a Flop ──────────────────────────────────
    print("\n  ── With a Board ──")
    print("  " + "─" * 40)

    result = calc.evaluate("AhKh", "QsQd", board="Th9h2c", iterations=20000)
    print(f"  AKhh vs QQ on Th9h2c (flush + straight draw):")
    print(f"    AKhh: {result.equities[0]:.1%} equity")
    print(f"    QQ:   {result.equities[1]:.1%} equity")

    # ── Hand vs Range ────────────────────────────────
    print("\n  ── Hand vs Range ──")
    print("  " + "─" * 40)

    result = calc.evaluate("AsKs", "QQ+,AKs", iterations=20000)
    print(f"  AKs vs {{QQ+, AKs}}:")
    print(f"    AKs:     {result.equities[0]:.1%} equity")
    print(f"    Range:   {result.equities[1]:.1%} equity")

    # ── Multi-way ────────────────────────────────────
    print("\n  ── Multi-way Pot ──")
    print("  " + "─" * 40)

    result = calc.evaluate("AhKh", "QsQd", "JcTc", iterations=20000)
    print(f"  AKs vs QQ vs JTs:")
    for hand, eq in zip(result.hands, result.equities):
        print(f"    {hand:<6} {eq:.1%}")

    # ── Range Analysis ───────────────────────────────
    print("\n  ── Range Analysis ──")
    print("  " + "─" * 40)

    parser = RangeParser()
    tight = parser.parse("QQ+,AKs")
    wide = parser.parse("77+,ATs+,KJs+,QJs,JTs")

    print(f"  Tight 3-bet range: {tight.num_combos} combos ({tight.pct_of_hands:.1f}% of hands)")
    print(f"  Wide opening range: {wide.num_combos} combos ({wide.pct_of_hands:.1f}% of hands)")

    print()


if __name__ == "__main__":
    main()
