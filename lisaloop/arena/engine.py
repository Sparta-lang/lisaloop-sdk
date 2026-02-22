"""
Arena — Tournament engine for pitting agents against each other.

Usage:
    from lisaloop import Arena, ArenaConfig
    from lisaloop.agents import LisaAgent, TAGAgent, RandomAgent

    arena = Arena(ArenaConfig(hands=10000, table_size=6))
    arena.register(LisaAgent())
    arena.register(TAGAgent())
    arena.register(RandomAgent())
    results = arena.run()
    arena.print_leaderboard()
"""

from __future__ import annotations

import io
import logging
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TextIO

from lisaloop.agents.base import Agent
from lisaloop.core.table import Table, TableConfig, HandResult

logger = logging.getLogger("lisaloop.arena")


@dataclass
class PlayerStats:
    """Tracked statistics for one agent in the arena."""
    name: str
    agent: Agent
    initial_stack: float = 0.0
    current_stack: float = 0.0
    hands_played: int = 0
    hands_won: int = 0
    total_profit: float = 0.0
    biggest_pot_won: float = 0.0
    showdowns: int = 0
    showdowns_won: int = 0
    vpip: int = 0  # voluntarily put in pot
    pfr: int = 0   # preflop raise
    three_bets: int = 0
    folds: int = 0
    all_ins: int = 0
    peak_stack: float = 0.0
    trough_stack: float = 0.0
    profit_history: List[float] = field(default_factory=list)

    @property
    def win_rate(self) -> float:
        return self.hands_won / max(1, self.hands_played)

    @property
    def bb_per_100(self) -> float:
        """Win rate in big blinds per 100 hands."""
        if self.hands_played == 0:
            return 0.0
        return (self.total_profit / 0.50) / self.hands_played * 100

    @property
    def vpip_pct(self) -> float:
        return self.vpip / max(1, self.hands_played) * 100

    @property
    def pfr_pct(self) -> float:
        return self.pfr / max(1, self.hands_played) * 100

    @property
    def showdown_win_pct(self) -> float:
        return self.showdowns_won / max(1, self.showdowns) * 100

    @property
    def roi(self) -> float:
        if self.initial_stack == 0:
            return 0.0
        return (self.total_profit / self.initial_stack) * 100


@dataclass
class MatchResult:
    """Complete results from an arena match."""
    hands_played: int
    duration_seconds: float
    leaderboard: List[PlayerStats]
    hand_results: List[HandResult]

    @property
    def winner(self) -> PlayerStats:
        return max(self.leaderboard, key=lambda p: p.total_profit)

    @property
    def hands_per_second(self) -> float:
        return self.hands_played / max(0.001, self.duration_seconds)


@dataclass
class ArenaConfig:
    hands: int = 1000
    table_size: int = 6
    small_blind: float = 0.25
    big_blind: float = 0.50
    starting_stack: float = 100.0
    seed: int | None = None
    verbose: bool = True
    log_interval: int = 100
    rebuy: bool = True
    rebuy_threshold: float = 20.0


class Arena:
    """
    Tournament engine. Register agents, run hands, track everything.

    Supports:
    - Round-robin and free-for-all formats
    - Live progress output with stats
    - Full hand history logging
    - Automatic rebuys (optional)
    - Comprehensive stat tracking (VPIP, PFR, BB/100, showdown %, etc.)
    """

    def __init__(self, config: ArenaConfig | None = None):
        self.config = config or ArenaConfig()
        self._agents: List[Agent] = []
        self._stats: Dict[str, PlayerStats] = {}
        self._results: List[HandResult] = []

    def register(self, agent: Agent) -> None:
        """Register an agent for the tournament."""
        if len(self._agents) >= self.config.table_size:
            raise ValueError(f"Table is full ({self.config.table_size} seats)")
        self._agents.append(agent)

    def run(self, output: TextIO | None = None) -> MatchResult:
        """Run the full tournament and return results."""
        if len(self._agents) < 2:
            raise RuntimeError("Need at least 2 agents to run arena.")

        out = output or sys.stdout
        table = Table(TableConfig(
            num_seats=self.config.table_size,
            small_blind=self.config.small_blind,
            big_blind=self.config.big_blind,
            seed=self.config.seed,
        ))

        # Seat players
        for i, agent in enumerate(self._agents):
            table.seat_player(i, agent, name=agent.name, stack=self.config.starting_stack)
            self._stats[agent.name] = PlayerStats(
                name=agent.name,
                agent=agent,
                initial_stack=self.config.starting_stack,
                current_stack=self.config.starting_stack,
                peak_stack=self.config.starting_stack,
                trough_stack=self.config.starting_stack,
            )

        if self.config.verbose:
            self._print_header(out)

        start_time = time.time()

        for hand_num in range(1, self.config.hands + 1):
            # Rebuy if needed
            if self.config.rebuy:
                for seat, info in table.seats.items():
                    if info.stack < self.config.rebuy_threshold:
                        rebuy_amount = self.config.starting_stack - info.stack
                        info.stack = self.config.starting_stack
                        stats = self._stats[info.name]
                        stats.total_profit -= rebuy_amount
                        stats.current_stack = info.stack

            # Notify agents
            for seat, info in table.seats.items():
                info.agent.on_hand_start(hand_num, info.stack)

            try:
                result = table.play_hand()
            except Exception as e:
                logger.warning(f"Hand {hand_num} error: {e}")
                continue

            self._results.append(result)
            self._update_stats(result, table)

            if self.config.verbose and hand_num % self.config.log_interval == 0:
                elapsed = time.time() - start_time
                self._print_progress(out, hand_num, elapsed)

        duration = time.time() - start_time

        if self.config.verbose:
            self._print_final(out, duration)

        leaderboard = sorted(self._stats.values(), key=lambda p: p.total_profit, reverse=True)

        return MatchResult(
            hands_played=len(self._results),
            duration_seconds=duration,
            leaderboard=leaderboard,
            hand_results=self._results,
        )

    def _update_stats(self, result: HandResult, table: Table) -> None:
        for seat, info in table.seats.items():
            stats = self._stats[info.name]
            stats.hands_played += 1
            stats.current_stack = info.stack

            if info.stack > stats.peak_stack:
                stats.peak_stack = info.stack
            if info.stack < stats.trough_stack:
                stats.trough_stack = info.stack

            if seat in result.winners:
                won = result.winners[seat]
                stats.hands_won += 1
                if won > stats.biggest_pot_won:
                    stats.biggest_pot_won = won

            if seat in result.showdown:
                stats.showdowns += 1
                if seat in result.winners:
                    stats.showdowns_won += 1

            stats.total_profit = stats.current_stack - stats.initial_stack
            stats.profit_history.append(stats.total_profit)

        # Track action-based stats from hand history
        for record in result.history:
            stats = self._stats.get(record.player_name)
            if not stats:
                continue
            from lisaloop.core.state import ActionType, Street
            if record.street == Street.PREFLOP:
                if record.action.type in (ActionType.CALL, ActionType.RAISE, ActionType.BET, ActionType.ALL_IN):
                    stats.vpip += 1
                if record.action.type in (ActionType.RAISE, ActionType.BET):
                    stats.pfr += 1
            if record.action.type == ActionType.FOLD:
                stats.folds += 1
            if record.action.type == ActionType.ALL_IN:
                stats.all_ins += 1

    def _print_header(self, out: TextIO) -> None:
        out.write("\n")
        out.write("╔══════════════════════════════════════════════════════════════╗\n")
        out.write("║                    LISA LOOP ARENA                          ║\n")
        out.write("╠══════════════════════════════════════════════════════════════╣\n")
        out.write(f"║  Hands: {self.config.hands:<8} | Blinds: ${self.config.small_blind}/{self.config.big_blind}          ║\n")
        out.write(f"║  Players: {len(self._agents):<6} | Starting stack: ${self.config.starting_stack:<8.2f}    ║\n")
        out.write("╠══════════════════════════════════════════════════════════════╣\n")
        for i, agent in enumerate(self._agents):
            out.write(f"║  Seat {i}: {agent.name:<20} v{agent.version:<8}              ║\n")
        out.write("╚══════════════════════════════════════════════════════════════╝\n")
        out.write("\n")
        out.flush()

    def _print_progress(self, out: TextIO, hand_num: int, elapsed: float) -> None:
        pct = hand_num / self.config.hands * 100
        hps = hand_num / max(0.001, elapsed)

        # Build compact leaderboard
        ranked = sorted(self._stats.values(), key=lambda p: p.total_profit, reverse=True)

        bar_len = 30
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)

        out.write(f"\r  [{bar}] {pct:5.1f}% | Hand {hand_num:,}/{self.config.hands:,} | {hps:.0f} hands/s | ")
        leader = ranked[0]
        trailer = ranked[-1]
        out.write(f"Leader: {leader.name} (+${leader.total_profit:.2f}) | Last: {trailer.name} (${trailer.total_profit:.2f})")
        out.flush()

    def _print_final(self, out: TextIO, duration: float = 0.0) -> None:
        out.write("\n\n")
        out.write("╔══════════════════════════════════════════════════════════════════════════════╗\n")
        out.write("║                              FINAL RESULTS                                 ║\n")
        out.write("╠════╦════════════════════╦══════════╦══════════╦═════════╦═══════╦═══════════╣\n")
        out.write("║ #  ║ Agent              ║ Profit   ║ BB/100   ║ Win %   ║ VPIP  ║ PFR       ║\n")
        out.write("╠════╬════════════════════╬══════════╬══════════╬═════════╬═══════╬═══════════╣\n")

        ranked = sorted(self._stats.values(), key=lambda p: p.total_profit, reverse=True)
        for i, stats in enumerate(ranked):
            profit_str = f"+${stats.total_profit:.2f}" if stats.total_profit >= 0 else f"-${abs(stats.total_profit):.2f}"
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f" {i+1}"
            out.write(
                f"║ {medal} ║ {stats.name:<18} ║ {profit_str:>8} ║ {stats.bb_per_100:>+7.1f} ║ {stats.win_rate*100:>5.1f}%  ║ {stats.vpip_pct:>4.1f}% ║ {stats.pfr_pct:>5.1f}%    ║\n"
            )

        out.write("╚════╩════════════════════╩══════════╩══════════╩═════════╩═══════╩═══════════╝\n")

        # Detailed stats
        out.write("\n  Detailed Stats:\n")
        out.write("  " + "─" * 70 + "\n")
        for stats in ranked:
            out.write(f"\n  {stats.name}:\n")
            out.write(f"    Hands: {stats.hands_played:,} | Won: {stats.hands_won:,} | Showdowns: {stats.showdowns} (won {stats.showdown_win_pct:.0f}%)\n")
            out.write(f"    Biggest pot: ${stats.biggest_pot_won:.2f} | Peak: ${stats.peak_stack:.2f} | Trough: ${stats.trough_stack:.2f}\n")
            out.write(f"    All-ins: {stats.all_ins} | Folds: {stats.folds} | ROI: {stats.roi:+.1f}%\n")

        out.write("\n")
        out.flush()

    def print_leaderboard(self, out: TextIO | None = None) -> None:
        """Print the current leaderboard."""
        self._print_final(out or sys.stdout)
