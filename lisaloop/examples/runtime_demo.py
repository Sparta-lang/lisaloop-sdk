"""
Runtime Demo — shows the full framework lifecycle.

Demonstrates: runtime, plugins, events, character files,
memory, and providers all working together.
"""

from lisaloop.runtime import AgentRuntime, RuntimeConfig
from lisaloop.events import EventType
from lisaloop.config import Character, CharacterLoader
from lisaloop.agents import LisaAgent, TAGAgent


def main():
    # ── Create Runtime ───────────────────────────────
    print("\n  ── Lisa Loop Framework Demo ──")
    print("  " + "═" * 50)

    runtime = AgentRuntime(RuntimeConfig(
        name="demo-session",
        seed=42,
        verbose=True,
        memory_enabled=False,  # Skip DB for demo
    ))

    # ── Subscribe to Events ──────────────────────────
    runtime.events.on(EventType.AGENT_REGISTERED, lambda e: (
        print(f"  [event] Agent registered: {e.data['agent']}")
    ))
    runtime.events.on(EventType.TOURNAMENT_END, lambda e: (
        print(f"  [event] Tournament complete! Winner: {e.data['winner']}")
    ))

    # ── Register Agents ──────────────────────────────
    runtime.register_agent(LisaAgent(seed=42))
    runtime.register_agent(TAGAgent(seed=42))

    # ── Load Agent from Character File ───────────────
    print("\n  Loading character from JSON...")
    duffman = Character(
        name="Duffman",
        style="tight-aggressive",
        aggression=0.85,
        tightness=0.85,
        bluff_frequency=0.10,
    )
    runtime.register_agent(duffman.to_agent(seed=42))

    # ── Run Tournament ───────────────────────────────
    print(f"\n  Running tournament with {len(runtime.agents)} agents...")
    result = runtime.run_arena(hands=2000)

    # ── Show Status ──────────────────────────────────
    print(f"\n  Runtime Status:")
    status = runtime.status()
    for key, val in status.items():
        print(f"    {key}: {val}")

    print()


if __name__ == "__main__":
    main()
