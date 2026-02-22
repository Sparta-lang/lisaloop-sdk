"""
Post-match analysis tools.

Usage:
    from lisaloop.analysis.stats import analyze_match, compare_agents

    report = analyze_match(result)
    comparison = compare_agents(result, "Lisa", "TAGBot")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from lisaloop.arena.engine import MatchResult, PlayerStats


@dataclass
class MatchReport:
    """Comprehensive match analysis report."""
    total_hands: int
    duration: float
    hands_per_second: float
    winner: str
    winner_profit: float
    player_reports: Dict[str, PlayerReport]
    biggest_pot: float
    avg_pot_size: float


@dataclass
class PlayerReport:
    """Detailed report for one player."""
    name: str
    profit: float
    bb_per_100: float
    vpip: float
    pfr: float
    win_rate: float
    showdown_win_rate: float
    avg_profit_per_hand: float
    profit_std_dev: float
    max_drawdown: float
    sharpe_ratio: float
    style: str


@dataclass
class HeadToHead:
    """Head-to-head comparison of two agents."""
    agent_a: str
    agent_b: str
    a_profit: float
    b_profit: float
    a_bb_per_100: float
    b_bb_per_100: float
    edge_bb_per_100: float
    confidence: str


def analyze_match(result: MatchResult) -> MatchReport:
    """Generate a full match report from arena results."""
    player_reports = {}

    for stats in result.leaderboard:
        # Calculate profit standard deviation
        if len(stats.profit_history) >= 2:
            mean = sum(stats.profit_history) / len(stats.profit_history)
            variance = sum((x - mean) ** 2 for x in stats.profit_history) / len(stats.profit_history)
            std_dev = variance ** 0.5
        else:
            std_dev = 0.0

        # Max drawdown
        max_drawdown = _calc_max_drawdown(stats.profit_history)

        # Sharpe-like ratio (profit per unit of risk)
        sharpe = stats.bb_per_100 / max(0.01, std_dev) if std_dev > 0 else 0.0

        # Classify play style
        style = _classify_style(stats)

        player_reports[stats.name] = PlayerReport(
            name=stats.name,
            profit=stats.total_profit,
            bb_per_100=stats.bb_per_100,
            vpip=stats.vpip_pct,
            pfr=stats.pfr_pct,
            win_rate=stats.win_rate * 100,
            showdown_win_rate=stats.showdown_win_pct,
            avg_profit_per_hand=stats.total_profit / max(1, stats.hands_played),
            profit_std_dev=std_dev,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            style=style,
        )

    total_pots = sum(r.pot_total for r in result.hand_results)
    avg_pot = total_pots / max(1, len(result.hand_results))
    biggest_pot = max((r.pot_total for r in result.hand_results), default=0)

    return MatchReport(
        total_hands=result.hands_played,
        duration=result.duration_seconds,
        hands_per_second=result.hands_per_second,
        winner=result.winner.name,
        winner_profit=result.winner.total_profit,
        player_reports=player_reports,
        biggest_pot=biggest_pot,
        avg_pot_size=avg_pot,
    )


def compare_agents(result: MatchResult, agent_a: str, agent_b: str) -> HeadToHead:
    """Compare two agents from a match result."""
    stats_a = next((s for s in result.leaderboard if s.name == agent_a), None)
    stats_b = next((s for s in result.leaderboard if s.name == agent_b), None)

    if not stats_a or not stats_b:
        raise ValueError(f"Agent not found in results.")

    edge = stats_a.bb_per_100 - stats_b.bb_per_100
    abs_edge = abs(edge)

    if abs_edge > 10:
        confidence = "high"
    elif abs_edge > 5:
        confidence = "medium"
    else:
        confidence = "low (need more hands)"

    return HeadToHead(
        agent_a=agent_a,
        agent_b=agent_b,
        a_profit=stats_a.total_profit,
        b_profit=stats_b.total_profit,
        a_bb_per_100=stats_a.bb_per_100,
        b_bb_per_100=stats_b.bb_per_100,
        edge_bb_per_100=edge,
        confidence=confidence,
    )


def _calc_max_drawdown(profit_history: List[float]) -> float:
    if not profit_history:
        return 0.0
    peak = profit_history[0]
    max_dd = 0.0
    for p in profit_history:
        if p > peak:
            peak = p
        dd = peak - p
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _classify_style(stats: PlayerStats) -> str:
    vpip = stats.vpip_pct
    pfr = stats.pfr_pct

    if vpip < 18 and pfr < 14:
        return "Nit"
    if vpip < 24 and pfr > 16:
        return "TAG (Tight-Aggressive)"
    if vpip > 30 and pfr > 22:
        return "LAG (Loose-Aggressive)"
    if vpip > 35 and pfr < 15:
        return "Calling Station"
    if vpip > 40:
        return "Maniac"
    return "Regular"
