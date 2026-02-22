"""
Self-play training loop — agents learn by playing against themselves.

Runs thousands of hands between agent copies, tracks performance
over time, and emits training events for monitoring.

Usage:
    from lisaloop.training import SelfPlayTrainer, TrainingConfig
    from lisaloop.agents import LisaAgent

    trainer = SelfPlayTrainer(TrainingConfig(
        epochs=10,
        hands_per_epoch=5000,
        seed=42,
    ))

    # Train against copies of self
    results = trainer.train(LisaAgent(seed=42))

    # Train against a pool of opponents
    results = trainer.train_against_pool(
        hero=LisaAgent(seed=42),
        opponents=[TAGAgent(), LAGAgent(), GTOApproxAgent()],
    )

    # Access training history
    for epoch in results:
        print(f"Epoch {epoch['epoch']}: {epoch['bb_per_100']:+.1f} BB/100")
"""

from __future__ import annotations

import copy
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from lisaloop.agents.base import Agent
from lisaloop.arena.engine import Arena, ArenaConfig

logger = logging.getLogger("lisaloop.training")


@dataclass
class TrainingConfig:
    """Configuration for self-play training."""
    epochs: int = 10
    hands_per_epoch: int = 5000
    table_size: int = 2
    small_blind: float = 0.25
    big_blind: float = 0.50
    starting_stack: float = 100.0
    seed: int | None = None
    verbose: bool = True
    on_epoch_complete: Optional[Callable] = None


class SelfPlayTrainer:
    """
    Self-play training engine.

    Runs repeated matches and tracks performance over time.
    Can train against self-copies or a pool of diverse opponents.
    """

    def __init__(self, config: TrainingConfig | None = None):
        self.config = config or TrainingConfig()
        self._history: List[Dict[str, Any]] = []

    def train(self, agent: Agent) -> List[Dict[str, Any]]:
        """
        Train an agent against a copy of itself.

        Returns training history: list of epoch results.
        """
        if self.config.verbose:
            print(f"\n  Self-Play Training: {agent.name}")
            print(f"  {'═' * 50}")
            print(f"  Epochs: {self.config.epochs} | Hands/epoch: {self.config.hands_per_epoch}")
            print()

        self._history = []

        for epoch in range(1, self.config.epochs + 1):
            # Create a fresh copy as opponent
            opponent = copy.deepcopy(agent)
            opponent.name = f"{agent.name}_shadow"

            result = self._run_epoch(agent, [opponent], epoch)
            self._history.append(result)

            if self.config.verbose:
                self._print_epoch(result)

            if self.config.on_epoch_complete:
                self.config.on_epoch_complete(result)

        if self.config.verbose:
            self._print_summary()

        return self._history

    def train_against_pool(
        self,
        hero: Agent,
        opponents: List[Agent],
    ) -> List[Dict[str, Any]]:
        """
        Train an agent against a pool of different opponents.

        Each epoch pits the hero against all opponents simultaneously
        or in round-robin fashion.
        """
        if self.config.verbose:
            opp_names = ", ".join(o.name for o in opponents)
            print(f"\n  Pool Training: {hero.name} vs [{opp_names}]")
            print(f"  {'═' * 50}")
            print()

        self._history = []

        for epoch in range(1, self.config.epochs + 1):
            result = self._run_epoch(hero, opponents, epoch)
            self._history.append(result)

            if self.config.verbose:
                self._print_epoch(result)

        if self.config.verbose:
            self._print_summary()

        return self._history

    def _run_epoch(
        self,
        hero: Agent,
        opponents: List[Agent],
        epoch: int,
    ) -> Dict[str, Any]:
        """Run one training epoch."""
        table_size = min(1 + len(opponents), self.config.table_size)

        config = ArenaConfig(
            hands=self.config.hands_per_epoch,
            table_size=table_size,
            small_blind=self.config.small_blind,
            big_blind=self.config.big_blind,
            starting_stack=self.config.starting_stack,
            seed=(self.config.seed + epoch) if self.config.seed else None,
            verbose=False,
        )

        arena = Arena(config)
        arena.register(hero)
        for opp in opponents[:table_size - 1]:
            arena.register(opp)

        start = time.time()
        result = arena.run()
        duration = time.time() - start

        # Find hero stats
        hero_stats = next(
            (s for s in result.leaderboard if s.name == hero.name), None
        )

        return {
            "epoch": epoch,
            "hands": result.hands_played,
            "duration": duration,
            "bb_per_100": hero_stats.bb_per_100 if hero_stats else 0,
            "profit": hero_stats.total_profit if hero_stats else 0,
            "vpip": hero_stats.vpip_pct if hero_stats else 0,
            "pfr": hero_stats.pfr_pct if hero_stats else 0,
            "win_rate": hero_stats.win_rate if hero_stats else 0,
            "hands_per_sec": result.hands_per_second,
        }

    def _print_epoch(self, result: Dict) -> None:
        bb = result["bb_per_100"]
        emoji = "+" if bb > 0 else "-"
        print(
            f"  Epoch {result['epoch']:>3}: "
            f"{emoji} {bb:>+7.1f} BB/100 | "
            f"${result['profit']:>+8.2f} | "
            f"VPIP: {result['vpip']:>4.1f}% | "
            f"{result['hands_per_sec']:.0f} h/s"
        )

    def _print_summary(self) -> None:
        if not self._history:
            return

        avg_bb = sum(h["bb_per_100"] for h in self._history) / len(self._history)
        total_hands = sum(h["hands"] for h in self._history)
        total_profit = sum(h["profit"] for h in self._history)

        print(f"\n  {'─' * 50}")
        print(f"  Total: {total_hands:,} hands | Avg: {avg_bb:+.1f} BB/100 | Net: ${total_profit:+.2f}")

        # Trend
        if len(self._history) >= 3:
            first_half = self._history[:len(self._history)//2]
            second_half = self._history[len(self._history)//2:]
            first_avg = sum(h["bb_per_100"] for h in first_half) / len(first_half)
            second_avg = sum(h["bb_per_100"] for h in second_half) / len(second_half)
            trend = "improving" if second_avg > first_avg else "declining"
            print(f"  Trend: {trend} ({first_avg:+.1f} → {second_avg:+.1f} BB/100)")

        print()

    @property
    def history(self) -> List[Dict]:
        return list(self._history)
