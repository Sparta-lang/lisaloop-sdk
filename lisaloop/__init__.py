"""
Lisa Loop SDK — The open framework for building on Lisa Loop.

Poker agents, equity calculators, strategy tools, analytics,
tournament engines, hand replays, and more.

Usage:
    from lisaloop import Agent, Arena, Table, GameState
    from lisaloop.agents import LisaAgent, RandomAgent, TAGAgent
    from lisaloop.equity import EquityCalculator, Range
    from lisaloop.strategy import BetSizer, PositionCharts, ICMCalculator
    from lisaloop.replay import HandReplay
"""

__version__ = "0.3.0"

from lisaloop.core.state import GameState, PlayerState, Action, ActionType, Street
from lisaloop.core.cards import Card, Hand, Deck, HandRank, HandEvaluator
from lisaloop.core.table import Table, TableConfig, Blind
from lisaloop.agents.base import Agent
from lisaloop.arena.engine import Arena, ArenaConfig, MatchResult

__all__ = [
    # Core
    "Agent",
    "Arena",
    "ArenaConfig",
    "MatchResult",
    "Table",
    "TableConfig",
    "Blind",
    "GameState",
    "PlayerState",
    "Action",
    "ActionType",
    "Street",
    "Card",
    "Hand",
    "Deck",
    "HandRank",
    "HandEvaluator",
]
