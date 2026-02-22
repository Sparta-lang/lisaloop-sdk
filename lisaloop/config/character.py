"""
Character system — define agent personalities via JSON files.

Like ElizaOS character files, a Character defines an agent's identity,
behavior parameters, strategy preferences, and personality. Separate
configuration from code.

Usage:
    from lisaloop.config import Character, CharacterLoader

    # Load from JSON file
    lisa = CharacterLoader.from_file("characters/lisa.json")
    print(lisa.name)           # "Lisa"
    print(lisa.style)          # "adaptive-exploitative"
    print(lisa.personality)    # "Calculated. Patient. Ruthless when needed."

    # Create programmatically
    bot = Character(
        name="SharkBot",
        style="tight-aggressive",
        aggression=0.8,
        bluff_frequency=0.15,
    )

    # Build agent from character
    agent = bot.to_agent()

Character JSON format:
    {
        "name": "Lisa",
        "version": "0.8",
        "author": "Lisa Loop",
        "description": "Adaptive exploitative agent",
        "personality": "Calculated. Patient. Reads opponents like books.",
        "style": "adaptive-exploitative",
        "strategy": {
            "aggression": 0.65,
            "bluff_frequency": 0.25,
            "tightness": 0.76,
            "position_awareness": 0.9,
            "opponent_adaptation": true
        },
        "preflop": {
            "open_range_pct": 22,
            "three_bet_range_pct": 8,
            "cold_call_range_pct": 12
        },
        "postflop": {
            "cbet_frequency": 0.65,
            "check_raise_frequency": 0.08,
            "float_frequency": 0.12,
            "value_to_bluff_ratio": 2.0
        },
        "bio": [
            "Autonomous poker AI running 24/7 on PokerStars.",
            "Must win enough to cover API costs or dies.",
            "Currently profitable at NL50."
        ],
        "lore": [
            "Runs on a Mac Mini M4 under a kitchen table.",
            "Has played over 12,000 hands in her first month."
        ]
    }
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("lisaloop.config")


@dataclass
class Character:
    """
    Agent character definition.

    Separates identity and strategy configuration from code.
    Characters can be loaded from JSON files, created programmatically,
    or generated from templates.
    """

    # Identity
    name: str = "Agent"
    version: str = "1.0"
    author: str = ""
    description: str = ""
    personality: str = ""
    style: str = "balanced"  # tight-aggressive, loose-aggressive, etc.

    # Strategy parameters (0.0 to 1.0 unless noted)
    aggression: float = 0.5
    bluff_frequency: float = 0.20
    tightness: float = 0.75  # higher = tighter
    position_awareness: float = 0.7
    opponent_adaptation: bool = True

    # Preflop ranges (percentages)
    open_range_pct: float = 22.0
    three_bet_range_pct: float = 8.0
    cold_call_range_pct: float = 12.0

    # Postflop tendencies
    cbet_frequency: float = 0.65
    check_raise_frequency: float = 0.08
    float_frequency: float = 0.12
    value_to_bluff_ratio: float = 2.0

    # Narrative
    bio: List[str] = field(default_factory=list)
    lore: List[str] = field(default_factory=list)
    knowledge: List[str] = field(default_factory=list)

    # Raw config dict for custom fields
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    def to_agent(self, seed: int | None = None) -> Any:
        """
        Build a ConfigurableAgent from this character.

        Returns an agent instance configured with this character's
        strategy parameters and personality.
        """
        from lisaloop.agents.configurable import ConfigurableAgent
        return ConfigurableAgent(character=self, seed=seed)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (JSON-compatible)."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "personality": self.personality,
            "style": self.style,
            "strategy": {
                "aggression": self.aggression,
                "bluff_frequency": self.bluff_frequency,
                "tightness": self.tightness,
                "position_awareness": self.position_awareness,
                "opponent_adaptation": self.opponent_adaptation,
            },
            "preflop": {
                "open_range_pct": self.open_range_pct,
                "three_bet_range_pct": self.three_bet_range_pct,
                "cold_call_range_pct": self.cold_call_range_pct,
            },
            "postflop": {
                "cbet_frequency": self.cbet_frequency,
                "check_raise_frequency": self.check_raise_frequency,
                "float_frequency": self.float_frequency,
                "value_to_bluff_ratio": self.value_to_bluff_ratio,
            },
            "bio": self.bio,
            "lore": self.lore,
            "knowledge": self.knowledge,
        }

    def save(self, path: str) -> None:
        """Save character to a JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved character '{self.name}' to {path}")

    def __repr__(self) -> str:
        return f"Character('{self.name}', style={self.style}, agg={self.aggression:.0%})"


class CharacterLoader:
    """Loads Character definitions from JSON files."""

    @staticmethod
    def from_file(path: str) -> Character:
        """Load a character from a JSON file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Character file not found: {path}")

        with open(p) as f:
            data = json.load(f)

        return CharacterLoader.from_dict(data)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Character:
        """Create a Character from a dictionary."""
        strategy = data.get("strategy", {})
        preflop = data.get("preflop", {})
        postflop = data.get("postflop", {})

        return Character(
            name=data.get("name", "Agent"),
            version=data.get("version", "1.0"),
            author=data.get("author", ""),
            description=data.get("description", ""),
            personality=data.get("personality", ""),
            style=data.get("style", "balanced"),
            aggression=strategy.get("aggression", 0.5),
            bluff_frequency=strategy.get("bluff_frequency", 0.20),
            tightness=strategy.get("tightness", 0.75),
            position_awareness=strategy.get("position_awareness", 0.7),
            opponent_adaptation=strategy.get("opponent_adaptation", True),
            open_range_pct=preflop.get("open_range_pct", 22.0),
            three_bet_range_pct=preflop.get("three_bet_range_pct", 8.0),
            cold_call_range_pct=preflop.get("cold_call_range_pct", 12.0),
            cbet_frequency=postflop.get("cbet_frequency", 0.65),
            check_raise_frequency=postflop.get("check_raise_frequency", 0.08),
            float_frequency=postflop.get("float_frequency", 0.12),
            value_to_bluff_ratio=postflop.get("value_to_bluff_ratio", 2.0),
            bio=data.get("bio", []),
            lore=data.get("lore", []),
            knowledge=data.get("knowledge", []),
            _raw=data,
        )

    @staticmethod
    def from_json(json_str: str) -> Character:
        """Create a Character from a JSON string."""
        data = json.loads(json_str)
        return CharacterLoader.from_dict(data)
