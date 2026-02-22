"""
Quickstart: Run your first arena in 10 lines.

    python -m lisaloop.examples.quickstart
"""

from lisaloop import Arena, ArenaConfig
from lisaloop.agents import LisaAgent, TAGAgent, LAGAgent, RandomAgent, GTOApproxAgent

arena = Arena(ArenaConfig(hands=2000, table_size=6, seed=42))

arena.register(LisaAgent(seed=42))
arena.register(TAGAgent(seed=42))
arena.register(LAGAgent(seed=42))
arena.register(GTOApproxAgent(seed=42))
arena.register(RandomAgent(seed=42))

result = arena.run()

print(f"\nWinner: {result.winner.name} with ${result.winner.total_profit:+.2f}")
print(f"Speed: {result.hands_per_second:.0f} hands/sec")
