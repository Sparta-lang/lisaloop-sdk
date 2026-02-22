"""
Lisa Loop SDK — Command Line Interface.

Usage:
    lisaloop arena --hands 10000 --agents lisa,tag,lag,random,gto
    lisaloop quickplay --hands 1000
    lisaloop benchmark --agent my_agent.py
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

from lisaloop.agents import LisaAgent, RandomAgent, TAGAgent, LAGAgent, GTOApproxAgent
from lisaloop.arena.engine import Arena, ArenaConfig
from lisaloop.analysis.stats import analyze_match, compare_agents


BUILTIN_AGENTS = {
    "lisa": LisaAgent,
    "random": RandomAgent,
    "tag": TAGAgent,
    "lag": LAGAgent,
    "gto": GTOApproxAgent,
}


def load_custom_agent(path: str):
    """Load a custom agent from a Python file."""
    from lisaloop.agents.base import Agent

    p = Path(path)
    if not p.exists():
        print(f"Error: file not found: {path}")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("custom_agent", p)
    module = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(module)  # type: ignore

    # Find the Agent subclass
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, Agent) and attr is not Agent:
            return attr()

    print(f"Error: no Agent subclass found in {path}")
    sys.exit(1)


def cmd_arena(args):
    """Run an arena tournament."""
    config = ArenaConfig(
        hands=args.hands,
        table_size=args.seats,
        small_blind=args.sb,
        big_blind=args.bb,
        starting_stack=args.stack,
        seed=args.seed,
        verbose=True,
        log_interval=max(1, args.hands // 20),
    )

    arena = Arena(config)

    # Register agents
    agent_names = [a.strip() for a in args.agents.split(",")]
    for name in agent_names:
        if name in BUILTIN_AGENTS:
            arena.register(BUILTIN_AGENTS[name](seed=args.seed))
        elif Path(name).exists():
            arena.register(load_custom_agent(name))
        else:
            print(f"Unknown agent: {name}")
            print(f"Built-in agents: {', '.join(BUILTIN_AGENTS.keys())}")
            print(f"Or provide a path to a .py file with an Agent subclass.")
            sys.exit(1)

    result = arena.run()

    if args.analyze:
        report = analyze_match(result)
        print(f"\n  Match Analysis:")
        print(f"  {'─' * 50}")
        print(f"  Average pot size: ${report.avg_pot_size:.2f}")
        print(f"  Biggest pot: ${report.biggest_pot:.2f}")
        print(f"  Speed: {report.hands_per_second:.0f} hands/sec")
        print()
        for name, pr in report.player_reports.items():
            print(f"  {name} — Style: {pr.style}")
            print(f"    Sharpe: {pr.sharpe_ratio:.2f} | Max Drawdown: ${pr.max_drawdown:.2f}")
        print()


def cmd_quickplay(args):
    """Quick 1v1: your agent vs Lisa."""
    config = ArenaConfig(
        hands=args.hands,
        table_size=2,
        seed=args.seed,
        verbose=True,
        log_interval=max(1, args.hands // 20),
    )

    arena = Arena(config)

    if args.agent and Path(args.agent).exists():
        arena.register(load_custom_agent(args.agent))
    else:
        arena.register(TAGAgent(seed=args.seed))

    arena.register(LisaAgent(seed=args.seed))
    result = arena.run()

    if result.leaderboard:
        winner = result.winner
        print(f"\n  Winner: {winner.name} with ${winner.total_profit:+.2f} profit")
        print(f"  BB/100: {winner.bb_per_100:+.1f}")


def cmd_benchmark(args):
    """Benchmark a custom agent against all built-in agents."""
    custom = load_custom_agent(args.agent)

    print(f"\n  Benchmarking: {custom.name}")
    print(f"  {'═' * 50}")

    results = {}
    for name, cls in BUILTIN_AGENTS.items():
        config = ArenaConfig(
            hands=args.hands,
            table_size=2,
            seed=args.seed,
            verbose=False,
        )
        arena = Arena(config)
        arena.register(custom.__class__(seed=args.seed))
        arena.register(cls(seed=args.seed))
        result = arena.run()

        custom_stats = next(s for s in result.leaderboard if s.name == custom.name)
        opponent_stats = next(s for s in result.leaderboard if s.name != custom.name)
        results[name] = custom_stats.bb_per_100

        emoji = "✓" if custom_stats.total_profit > 0 else "✗"
        print(f"  {emoji} vs {name:<12} | {custom_stats.bb_per_100:>+7.1f} BB/100 | ${custom_stats.total_profit:>+8.2f}")

    avg_bb = sum(results.values()) / len(results)
    print(f"\n  Average: {avg_bb:+.1f} BB/100")

    if avg_bb > 5:
        print("  Verdict: Strong agent! Lisa would be proud.")
    elif avg_bb > 0:
        print("  Verdict: Profitable. Keep grinding.")
    elif avg_bb > -5:
        print("  Verdict: Marginal. Needs work.")
    else:
        print("  Verdict: Losing player. Back to the lab.")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="lisaloop",
        description="Lisa Loop SDK — Build poker agents that think.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Arena
    arena_parser = subparsers.add_parser("arena", help="Run a multi-agent tournament")
    arena_parser.add_argument("--hands", type=int, default=1000, help="Number of hands (default: 1000)")
    arena_parser.add_argument("--agents", type=str, default="lisa,tag,lag,random", help="Comma-separated agents")
    arena_parser.add_argument("--seats", type=int, default=6, help="Table size (default: 6)")
    arena_parser.add_argument("--sb", type=float, default=0.25, help="Small blind")
    arena_parser.add_argument("--bb", type=float, default=0.50, help="Big blind")
    arena_parser.add_argument("--stack", type=float, default=100.0, help="Starting stack")
    arena_parser.add_argument("--seed", type=int, default=None, help="Random seed")
    arena_parser.add_argument("--analyze", action="store_true", help="Print detailed analysis")
    arena_parser.set_defaults(func=cmd_arena)

    # Quick play
    quick_parser = subparsers.add_parser("quickplay", help="Quick 1v1 vs Lisa")
    quick_parser.add_argument("--hands", type=int, default=1000, help="Number of hands")
    quick_parser.add_argument("--agent", type=str, default=None, help="Path to custom agent .py file")
    quick_parser.add_argument("--seed", type=int, default=None, help="Random seed")
    quick_parser.set_defaults(func=cmd_quickplay)

    # Benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Benchmark agent vs all built-ins")
    bench_parser.add_argument("agent", type=str, help="Path to custom agent .py file")
    bench_parser.add_argument("--hands", type=int, default=5000, help="Hands per matchup")
    bench_parser.add_argument("--seed", type=int, default=None, help="Random seed")
    bench_parser.set_defaults(func=cmd_benchmark)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
