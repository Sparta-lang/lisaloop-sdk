"""Tests for the arena engine."""

import io
from lisaloop.arena.engine import Arena, ArenaConfig
from lisaloop.agents import RandomAgent, TAGAgent, LisaAgent


def test_arena_basic():
    arena = Arena(ArenaConfig(hands=50, table_size=3, seed=42, verbose=False))
    arena.register(RandomAgent(seed=1))
    arena.register(RandomAgent(seed=2))
    arena.register(TAGAgent(seed=3))
    result = arena.run(output=io.StringIO())
    assert result.hands_played == 50
    assert len(result.leaderboard) == 3


def test_arena_heads_up():
    arena = Arena(ArenaConfig(hands=100, table_size=2, seed=42, verbose=False))
    arena.register(LisaAgent(seed=1))
    arena.register(RandomAgent(seed=2))
    result = arena.run(output=io.StringIO())
    assert result.hands_played == 100
    assert result.winner is not None


def test_arena_stats_tracked():
    arena = Arena(ArenaConfig(hands=200, table_size=2, seed=42, verbose=False))
    arena.register(TAGAgent(seed=1))
    arena.register(RandomAgent(seed=2))
    result = arena.run(output=io.StringIO())

    for stats in result.leaderboard:
        assert stats.hands_played == 200
        assert stats.name in ("TAGBot", "RandomBot")
