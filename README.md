<p align="center">
  <h1 align="center">Lisa Loop SDK</h1>
</p>

<p align="center">
  <strong>Build poker agents that think.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/Status-Hackathon_Ready-00ff88?style=flat-square" alt="Status" />
</p>

---

The official SDK for building poker AI agents on the Lisa Loop platform. Create custom poker bots, pit them against each other in the arena, and benchmark against Lisa — the autonomous poker AI that grinds real money tables 24/7.

## Quickstart

```bash
pip install -e .
```

### 10 Lines to Your First Tournament

```python
from lisaloop import Arena, ArenaConfig
from lisaloop.agents import LisaAgent, TAGAgent, LAGAgent, RandomAgent, GTOApproxAgent

arena = Arena(ArenaConfig(hands=2000, table_size=6, seed=42))

arena.register(LisaAgent(seed=42))
arena.register(TAGAgent(seed=42))
arena.register(LAGAgent(seed=42))
arena.register(GTOApproxAgent(seed=42))
arena.register(RandomAgent(seed=42))

result = arena.run()
```

Output:

```
╔══════════════════════════════════════════════════════════════╗
║                    LISA LOOP ARENA                          ║
╠══════════════════════════════════════════════════════════════╣
║  Hands: 2000     | Blinds: $0.25/$0.5                      ║
║  Players: 5      | Starting stack: $100.00                  ║
╠══════════════════════════════════════════════════════════════╣
║  Seat 0: Lisa                 v0.8                          ║
║  Seat 1: TAGBot               v1.0                          ║
║  Seat 2: LAGBot               v1.0                          ║
║  Seat 3: GTOBot               v1.0                          ║
║  Seat 4: RandomBot            v1.0                          ║
╚══════════════════════════════════════════════════════════════╝
```

## Build Your Own Agent

Subclass `Agent` and implement `decide()`. That's it.

```python
from lisaloop import Agent, GameState, Action, ActionType, Street

class MyAgent(Agent):
    name = "MyBot"
    version = "1.0"
    author = "You"

    def decide(self, state: GameState) -> Action:
        # state.my_hand      → your hole cards
        # state.board         → community cards
        # state.pot.total     → pot size
        # state.pot_odds      → pot odds as ratio
        # state.position      → position (0=SB, higher=later)
        # state.valid_actions → all legal actions
        # state.street        → PREFLOP, FLOP, TURN, RIVER

        if state.street == Street.PREFLOP:
            # Play pocket pairs and high cards
            if state.my_hand.is_pair or max(c.rank.value for c in state.my_hand.cards) >= 12:
                return Action.raise_to(state.big_blind * 3)

        # Bet with pairs on the board
        if state.board:
            my_ranks = {c.rank for c in state.my_hand.cards}
            board_ranks = {c.rank for c in state.board}
            if my_ranks & board_ranks:
                return Action.bet(state.pot.total * 0.66)

        if state.can_check():
            return Action.check()
        return Action.fold()
```

### Run It

```bash
# 1v1 vs Lisa
lisaloop quickplay --agent my_agent.py --hands 5000

# Benchmark vs all built-in agents
lisaloop benchmark my_agent.py --hands 10000

# Full tournament
lisaloop arena --agents lisa,tag,lag,gto,random,my_agent.py --hands 10000
```

## Game State API

Everything your agent needs to make a decision:

```python
state.my_hand           # Hand([A♠, K♥])
state.board             # [T♠, 9♣, 2♦]
state.street            # Street.FLOP
state.pot.total         # 150.0
state.my_stack          # 485.0
state.current_bet       # 50.0
state.valid_actions     # [FOLD, CALL $50.00, RAISE $100.00]
state.position          # 2 (0=SB, 1=BB, 2=UTG, ...)
state.num_players       # 6
state.is_heads_up       # False
state.pot_odds          # 0.25 (need 25% equity to call)
state.stack_to_pot_ratio # 3.2 (SPR)
state.history           # all actions this hand
state.street_history    # actions on current street only
state.can_check()       # True/False
state.can_raise()       # True/False
```

## Actions

```python
Action.fold()                    # Give up
Action.check()                   # Pass (when no bet to you)
Action.call(amount)              # Match the current bet
Action.bet(amount)               # Open bet (when no bet yet)
Action.raise_to(amount)          # Raise to a total amount
Action.all_in(amount)            # Ship it
```

Invalid actions are auto-corrected — amounts get clamped to valid ranges, illegal actions default to check/fold.

## Built-in Agents

| Agent | Style | VPIP | Description |
|-------|-------|------|-------------|
| `LisaAgent` | Adaptive | ~24% | Opponent modeling, exploitative play, dynamic bluff frequencies |
| `TAGBot` | Tight-Aggressive | ~20% | Few hands, played hard. C-bets, fit-or-fold postflop |
| `LAGBot` | Loose-Aggressive | ~35% | Wide range, constant pressure, high bluff frequency |
| `GTOBot` | Balanced | ~22% | Mixed strategies, pot-geometric sizing, minimum defense frequency |
| `RandomBot` | Chaotic | ~50% | Random actions. The baseline to beat |

## Agent Lifecycle Hooks

Override these for stateful agents:

```python
class SmartAgent(Agent):
    def on_hand_start(self, hand_number: int, my_stack: float) -> None:
        """Called before each hand. Reset per-hand state here."""
        pass

    def on_hand_end(self, result: dict) -> None:
        """Called after each hand. result has 'won', 'profit', 'showdown' keys."""
        pass

    def on_opponent_action(self, player_name: str, action: Action, street: int) -> None:
        """Called when any opponent acts. Build opponent models here."""
        pass
```

## Arena Configuration

```python
ArenaConfig(
    hands=10000,           # Total hands to play
    table_size=6,          # 2-6 players
    small_blind=0.25,      # SB
    big_blind=0.50,        # BB
    starting_stack=100.0,  # 200BB deep
    seed=42,               # Reproducible results
    rebuy=True,            # Auto-rebuy when short
    rebuy_threshold=20.0,  # Rebuy below this stack
    verbose=True,          # Live progress output
    log_interval=100,      # Print every N hands
)
```

## Analysis

```python
from lisaloop.analysis.stats import analyze_match, compare_agents

report = analyze_match(result)
print(report.winner)
print(report.avg_pot_size)

for name, player in report.player_reports.items():
    print(f"{name}: {player.style} | Sharpe: {player.sharpe_ratio:.2f}")

# Head-to-head comparison
h2h = compare_agents(result, "Lisa", "MyBot")
print(f"Edge: {h2h.edge_bb_per_100:+.1f} BB/100 ({h2h.confidence})")
```

## CLI

```bash
# Multi-agent tournament with analysis
lisaloop arena --hands 10000 --agents lisa,tag,lag,gto,random --analyze

# Quick 1v1 heads-up
lisaloop quickplay --hands 5000

# Benchmark your agent against everyone
lisaloop benchmark my_agent.py --hands 10000
```

## Project Structure

```
lisaloop/
├── core/
│   ├── cards.py          # Card, Hand, Deck, HandEvaluator
│   ├── state.py          # GameState, Action, PlayerState
│   └── table.py          # Full poker table simulation
├── agents/
│   ├── base.py           # Agent base class (subclass this!)
│   ├── lisa_agent.py     # Lisa — adaptive, exploitative
│   ├── tag_agent.py      # Tight-Aggressive baseline
│   ├── lag_agent.py      # Loose-Aggressive baseline
│   ├── gto_agent.py      # GTO approximation
│   └── random_agent.py   # Random baseline
├── arena/
│   └── engine.py         # Tournament runner + leaderboard
├── analysis/
│   └── stats.py          # Post-match analysis + comparisons
├── examples/
│   ├── my_first_agent.py # Starter template
│   └── quickstart.py     # 10-line demo
├── cli.py                # Command-line interface
└── tests/
    ├── test_cards.py
    └── test_arena.py
```

## Hackathon Tracks

| Track | Challenge |
|-------|-----------|
| **Beat Lisa** | Build an agent that profits against Lisa over 10,000 hands |
| **Survival Mode** | Given $100, burn API credits per decision — last agent standing wins |
| **Read the Table** | Best opponent modeling system |
| **Coach Lisa** | Best post-session analysis tool |
| **New Game** | Adapt the SDK for Omaha, Short Deck, or tournaments |

---

<p align="center">
  <strong>The loop never breaks.</strong>
</p>

<p align="center">
  <sub>Built by <a href="https://github.com/LisaLoopBot">Lisa Loop</a></sub>
</p>
