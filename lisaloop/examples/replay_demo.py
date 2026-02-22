"""
Hand Replay Demo — Step-by-step hand visualization.

Runs a short match and replays interesting hands with ASCII art.
"""

from lisaloop import Arena, ArenaConfig
from lisaloop.agents import LisaAgent, TAGAgent, LAGAgent
from lisaloop.replay import HandReplay


def main():
    # Run a quick match
    arena = Arena(ArenaConfig(hands=100, table_size=3, seed=42, verbose=False))
    arena.register(LisaAgent(seed=42))
    arena.register(TAGAgent(seed=42))
    arena.register(LAGAgent(seed=42))
    result = arena.run()

    # Find the biggest pot
    if not result.hand_results:
        print("No hands played!")
        return

    biggest = max(result.hand_results, key=lambda h: h.pot_total)

    print("\n  Replaying the biggest pot from the match...\n")
    replay = HandReplay(biggest)
    replay.show()

    # Show summaries of last 5 hands
    print("\n  Last 5 hands:")
    print("  " + "─" * 60)
    for hand in result.hand_results[-5:]:
        print("  ", end="")
        HandReplay(hand).show_summary()


if __name__ == "__main__":
    main()
