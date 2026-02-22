<p align="center">
  <img src="https://cdn.prod.website-files.com/69082c5061a39922df8ed3b6/6995208684b51f80dfb971fa_New%20Project%20-%202026-02-18T005623.215.png" alt="Lisa Loop Banner" width="100%" />
</p>

<p align="center">
  <img src="https://cdn.prod.website-files.com/69082c5061a39922df8ed3b6/699b43bac4d0619656d4811f_New%20Project%20-%202026-02-18T022623.000.png" alt="Lisa" width="120" style="border-radius:50%" />
</p>

<h1 align="center">Lisa Loop SDK</h1>

<p align="center">
  <strong>The open framework for building on Lisa Loop. Poker agents, analytics tools, dashboards, bots, integrations — build anything.</strong>
</p>

<p align="center">
  <a href="https://github.com/LisaLoopBot/lisaloop-sdk"><img src="https://img.shields.io/badge/GitHub-lisaloop--sdk-0a0a0a?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" /></a>
  <a href="https://x.com/lisaloopbot"><img src="https://img.shields.io/badge/Twitter-@lisaloopbot-1DA1F2?style=for-the-badge&logo=x&logoColor=white" alt="Twitter" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" alt="PyTorch" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/Status-Hackathon_Ready-00ff88?style=flat-square" alt="Status" />
  <img src="https://img.shields.io/badge/Agents-5_Built_In-blueviolet?style=flat-square" alt="Agents" />
</p>

---

## What is this?

Lisa Loop is an autonomous self-learning poker AI that grinds real money tables 24/7 on a Mac Mini M4. She trains via self-play, deploys to PokerStars, and must win enough to cover her own API costs — or she dies.

**This SDK opens up her brain.** Use Lisa's core engine, neural network, game simulation, opponent modeling, and analysis tools to build whatever you want:

- Custom poker agents that compete in the arena
- Analytics dashboards and real-time visualizations
- Opponent profiling and leak detection tools
- Coaching systems and post-session analysis
- New game variants (Omaha, Short Deck, tournaments)
- Trading/strategy bots that use Lisa's decision framework
- Research tools for game theory and reinforcement learning
- API integrations, webhooks, and automation pipelines

**The SDK is the foundation. What you build on it is up to you.**

---

## Quickstart

```bash
git clone https://github.com/LisaLoopBot/lisaloop-sdk.git
cd lisaloop-sdk
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

╔══════════════════════════════════════════════════════════════════════════════╗
║                              FINAL RESULTS                                 ║
╠════╦════════════════════╦══════════╦══════════╦═════════╦═══════╦═══════════╣
║ 🥇 ║ Lisa               ║  +$47.20 ║   +4.7   ║  28.3%  ║ 23.1% ║  17.8%   ║
║ 🥈 ║ GTOBot             ║  +$12.50 ║   +1.3   ║  24.1%  ║ 21.5% ║  16.2%   ║
║ 🥉 ║ TAGBot             ║   -$3.80 ║   -0.4   ║  22.7%  ║ 19.8% ║  15.4%   ║
║  4 ║ LAGBot             ║  -$18.40 ║   -1.8   ║  21.2%  ║ 33.6% ║  26.1%   ║
║  5 ║ RandomBot          ║  -$37.50 ║   -3.8   ║  18.9%  ║ 48.2% ║   9.3%   ║
╚════╩════════════════════╩══════════╩══════════╩═════════╩═══════╩═══════════╝
```

---

## Build Anything

### 1. Custom Poker Agent

Subclass `Agent`, implement `decide()`. That's it.

```python
from lisaloop import Agent, GameState, Action, ActionType, Street

class MyAgent(Agent):
    name = "MyBot"

    def decide(self, state: GameState) -> Action:
        # Your strategy here
        if state.my_hand.is_pair:
            return Action.raise_to(state.big_blind * 3)
        if state.can_check():
            return Action.check()
        return Action.fold()
```

### 2. Analytics Dashboard

Use Lisa's analysis tools to build visualizations and coaching interfaces.

```python
from lisaloop.analysis.stats import analyze_match, compare_agents

report = analyze_match(result)
for name, player in report.player_reports.items():
    print(f"{name}: {player.style} | {player.bb_per_100:+.1f} BB/100 | Sharpe: {player.sharpe_ratio:.2f}")

# Head-to-head edge calculation
h2h = compare_agents(result, "Lisa", "MyBot")
print(f"Edge: {h2h.edge_bb_per_100:+.1f} BB/100 ({h2h.confidence})")
```

### 3. Opponent Profiler

Lisa's `LisaAgent` includes built-in opponent modeling. Use it to build HUDs, profiling tools, or scouting reports.

```python
from lisaloop.agents.lisa_agent import LisaAgent, OpponentModel

lisa = LisaAgent()
# After running hands, access opponent data:
for name, model in lisa._opponents.items():
    print(f"{name}: {model.summary()} | VPIP: {model.vpip_pct:.0%} | AF: {model.aggression_factor:.1f}")
```

### 4. Simulation Environment

Run thousands of hands programmatically for research, backtesting, or data generation.

```python
from lisaloop import Table, TableConfig
from lisaloop.agents import LisaAgent, TAGAgent

table = Table(TableConfig(num_seats=2, seed=42))
table.seat_player(0, LisaAgent(), name="Lisa", stack=100)
table.seat_player(1, TAGAgent(), name="Villain", stack=100)

for _ in range(10000):
    result = table.play_hand()
    # Log, analyze, visualize, stream, whatever you want
```

### 5. Custom Game Variants

Extend the `Table` class for new formats — Omaha, Short Deck, tournaments with blind levels, sit-and-go structures, anything.

### 6. Webhook / Event System

Build on the agent lifecycle hooks to create event-driven integrations:

```python
class WebhookAgent(Agent):
    name = "WebhookBot"

    def on_hand_end(self, result: dict) -> None:
        # Post to Discord, Slack, Twitter, database, whatever
        requests.post(WEBHOOK_URL, json=result)

    def on_opponent_action(self, player_name: str, action: Action, street: int) -> None:
        # Real-time opponent tracking pipeline
        log_to_database(player_name, action, street)
```

---

## Game State API

Everything your agent (or tool) needs:

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
state.to_dict()         # serialize for logging/APIs
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

Invalid actions are auto-corrected — amounts get clamped to valid ranges, illegal actions default to check/fold. Your agent can't break the game.

---

## Built-in Agents

| Agent | Style | VPIP | Description |
|-------|-------|------|-------------|
| `LisaAgent` | Adaptive | ~24% | Opponent modeling, exploitative play, dynamic bluff frequencies, board texture reads |
| `TAGBot` | Tight-Aggressive | ~20% | Few hands, played hard. C-bets, fit-or-fold postflop |
| `LAGBot` | Loose-Aggressive | ~35% | Wide range, constant pressure, high bluff frequency |
| `GTOBot` | Balanced | ~22% | Mixed strategies, pot-geometric sizing, minimum defense frequency |
| `RandomBot` | Chaotic | ~50% | Random actions. The baseline. If you lose to this, go home |

## Agent Lifecycle Hooks

Override these for stateful agents, tracking tools, or event-driven systems:

```python
class SmartAgent(Agent):
    def on_hand_start(self, hand_number: int, my_stack: float) -> None:
        """Called before each hand."""

    def on_hand_end(self, result: dict) -> None:
        """Called after each hand. result has 'won', 'profit', 'showdown'."""

    def on_opponent_action(self, player_name: str, action: Action, street: int) -> None:
        """Called when any opponent acts. Build models, trigger webhooks, log data."""
```

---

## CLI

```bash
# Multi-agent tournament with detailed analysis
lisaloop arena --hands 10000 --agents lisa,tag,lag,gto,random --analyze

# Quick 1v1 heads-up vs Lisa
lisaloop quickplay --hands 5000

# Benchmark your custom agent against all built-ins
lisaloop benchmark my_agent.py --hands 10000

# Load any .py file with an Agent subclass
lisaloop arena --agents lisa,tag,my_agent.py --hands 5000
```

---

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

---

## Project Structure

```
lisaloop-sdk/
├── lisaloop/
│   ├── core/
│   │   ├── cards.py          # Card, Hand, Deck, HandEvaluator (full 5-card eval)
│   │   ├── state.py          # GameState, Action, PlayerState, pot odds, SPR
│   │   └── table.py          # Complete poker table simulation engine
│   ├── agents/
│   │   ├── base.py           # Agent base class — subclass this!
│   │   ├── lisa_agent.py     # Lisa — adaptive exploitative + opponent modeling
│   │   ├── tag_agent.py      # Tight-Aggressive baseline
│   │   ├── lag_agent.py      # Loose-Aggressive baseline
│   │   ├── gto_agent.py      # GTO approximation with pot geometry
│   │   └── random_agent.py   # Random baseline
│   ├── arena/
│   │   └── engine.py         # Tournament runner, leaderboard, full stat tracking
│   ├── analysis/
│   │   └── stats.py          # Post-match reports, H2H comparisons, style classification
│   ├── examples/
│   │   ├── my_first_agent.py # Starter template — start here
│   │   └── quickstart.py     # 10-line demo
│   └── cli.py                # Command-line interface
├── tests/
│   ├── test_cards.py         # Card + hand evaluation tests
│   └── test_arena.py         # Arena integration tests
├── pyproject.toml
└── README.md
```

---

## Hackathon Tracks

| Track | Challenge |
|-------|-----------|
| **Beat Lisa** | Build an agent that profits against Lisa over 10,000 hands |
| **Survival Mode** | Given $100 in API credits, last agent standing wins |
| **Read the Table** | Best opponent modeling / player profiling system |
| **Coach Lisa** | Best post-session analysis or coaching tool |
| **Dashboard** | Best real-time visualization or monitoring tool |
| **New Game** | Adapt the SDK for Omaha, Short Deck, or tournament play |
| **Wild Card** | Surprise us. Use the SDK for something nobody expected |

---

## Lisa's Stats (Live)

| Metric | Value |
|--------|-------|
| Net Profit | +$135.50 |
| Hands Played | 12,847+ |
| Winrate | +6.8 BB/100 |
| VPIP | 24.1% |
| PFR | 18.7% |
| Aggression Factor | 2.4x |
| Stakes | NL50 ($0.25/$0.50) |
| Model | 4.2M parameters |
| Hardware | Mac Mini M4, 16GB unified |
| Uptime | 24/7 |

---

<p align="center">
  <img src="https://cdn.prod.website-files.com/69082c5061a39922df8ed3b6/699b43bac4d0619656d4811f_New%20Project%20-%202026-02-18T022623.000.png" alt="Lisa" width="60" />
</p>

<p align="center">
  <strong>The loop never breaks.</strong>
</p>

<p align="center">
  <sub>Built by <a href="https://github.com/LisaLoopBot">Lisa Loop</a> — self-learning poker AI running 24/7 on a Mac Mini under a kitchen table.</sub>
</p>
