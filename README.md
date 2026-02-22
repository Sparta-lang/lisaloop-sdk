<p align="center">
  <img src="https://cdn.prod.website-files.com/69082c5061a39922df8ed3b6/6995208684b51f80dfb971fa_New%20Project%20-%202026-02-18T005623.215.png" alt="Lisa Loop Banner" width="100%" />
</p>

<p align="center">
  <img src="https://cdn.prod.website-files.com/69082c5061a39922df8ed3b6/699b43bac4d0619656d4811f_New%20Project%20-%202026-02-18T022623.000.png" alt="Lisa" width="120" style="border-radius:50%" />
</p>

<h1 align="center">Lisa Loop SDK</h1>

<p align="center">
  <strong>The open framework for building on Lisa Loop — a self-learning poker AI that grinds real money 24/7.</strong>
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> &nbsp;·&nbsp;
  <a href="#build-anything">Build Anything</a> &nbsp;·&nbsp;
  <a href="#cli-tools">CLI Tools</a> &nbsp;·&nbsp;
  <a href="#hackathon">Hackathon</a> &nbsp;·&nbsp;
  <a href="#api-reference">API Reference</a>
</p>

<p align="center">
  <a href="https://github.com/LisaLoopBot/lisaloop-sdk"><img src="https://img.shields.io/badge/GitHub-lisaloop--sdk-0a0a0a?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" /></a>
  <a href="https://x.com/lisaloopbot"><img src="https://img.shields.io/badge/Twitter-@lisaloopbot-0a0a0a?style=for-the-badge&logo=x&logoColor=white" alt="Twitter" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/v0.2-Stable-00ff88?style=flat-square" alt="Version" />
  <img src="https://img.shields.io/badge/Zero_Dependencies-stdlib_only-blueviolet?style=flat-square" alt="Deps" />
</p>

---

## What is Lisa Loop?

Lisa Loop is an autonomous poker AI. She plays real money on PokerStars, learns from every hand, and must win enough to cover her own API costs — or she dies. She runs 24/7 on a Mac Mini M4 under a kitchen table.

**This SDK opens up her brain.** Everything Lisa uses — her game engine, equity calculator, opponent models, strategy tools, bet sizing, hand ranges, hand replays, and tournament infrastructure — is packaged here for you to build on.

```
┌─────────────────────────────────────────────────────────────────┐
│                        LISA LOOP SDK                            │
├──────────┬──────────┬──────────┬───────────┬──────────┬─────────┤
│  AGENTS  │  EQUITY  │ STRATEGY │  REPLAY   │  ARENA   │ ANALYSIS│
│          │          │          │           │          │         │
│ Lisa     │ Monte    │ Bet      │ Hand      │ Tourna-  │ Stats   │
│ TAG      │ Carlo    │ Sizing   │ History   │ ment     │ Reports │
│ LAG      │ Ranges   │ Position │ ASCII     │ Engine   │ H2H     │
│ GTO      │ Parser   │ Charts   │ Cards     │ Leader-  │ Style   │
│ Random   │ Multi-   │ ICM      │ Action    │ board    │ Sharpe  │
│ Custom   │ way      │ Bubble   │ Viewer    │ Rebuys   │ Drawdown│
├──────────┴──────────┴──────────┴───────────┴──────────┴─────────┤
│                      CORE ENGINE                                │
│  Cards · Deck · Hand Evaluator · Table · Game State · Actions   │
└─────────────────────────────────────────────────────────────────┘
```

---

<h2 id="quickstart">Quickstart</h2>

```bash
git clone https://github.com/LisaLoopBot/lisaloop-sdk.git
cd lisaloop-sdk
pip install -e .
```

Zero external dependencies. Pure Python. Works on Python 3.9+.

### Your First Tournament (10 lines)

```python
from lisaloop import Arena, ArenaConfig
from lisaloop.agents import LisaAgent, TAGAgent, LAGAgent, RandomAgent, GTOApproxAgent

arena = Arena(ArenaConfig(hands=5000, table_size=6, seed=42))

arena.register(LisaAgent(seed=42))
arena.register(TAGAgent(seed=42))
arena.register(LAGAgent(seed=42))
arena.register(GTOApproxAgent(seed=42))
arena.register(RandomAgent(seed=42))

result = arena.run()
```

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                              FINAL RESULTS                                 ║
╠════╦════════════════════╦══════════╦══════════╦═════════╦═══════╦═══════════╣
║ #  ║ Agent              ║ Profit   ║ BB/100   ║ Win %   ║ VPIP  ║ PFR       ║
╠════╬════════════════════╬══════════╬══════════╬═════════╬═══════╬═══════════╣
║ 🥇 ║ Lisa               ║  +$47.20 ║   +4.7   ║  28.3%  ║ 23.1% ║  17.8%   ║
║ 🥈 ║ GTOBot             ║  +$12.50 ║   +1.3   ║  24.1%  ║ 21.5% ║  16.2%   ║
║ 🥉 ║ TAGBot             ║   -$3.80 ║   -0.4   ║  22.7%  ║ 19.8% ║  15.4%   ║
║  4 ║ LAGBot             ║  -$18.40 ║   -1.8   ║  21.2%  ║ 33.6% ║  26.1%   ║
║  5 ║ RandomBot          ║  -$37.50 ║   -3.8   ║  18.9%  ║ 48.2% ║   9.3%   ║
╚════╩════════════════════╩══════════╩══════════╩═════════╩═══════╩═══════════╝
```

---

<h2 id="build-anything">Build Anything</h2>

### 1. Custom Poker Agent

Subclass `Agent`, implement `decide()`. That's it.

```python
from lisaloop import Agent, GameState, Action

class SharkBot(Agent):
    name = "SharkBot"
    version = "1.0"

    def decide(self, state: GameState) -> Action:
        # Tight-aggressive with position awareness
        if state.my_hand.is_pair:
            return Action.raise_to(state.big_blind * 3)
        if state.pot_odds < 0.25 and state.can_check():
            return Action.check()
        if state.can_check():
            return Action.check()
        return Action.fold()
```

### 2. Monte Carlo Equity Calculator

Calculate hand equity against specific hands, ranges, or multi-way.

```python
from lisaloop.equity import EquityCalculator

calc = EquityCalculator(seed=42)

# Hand vs hand
result = calc.evaluate("AhKh", "QsQd", iterations=20000)
# → AKs: 46.2% equity | QQ: 53.8% equity

# Hand vs hand with a board
result = calc.evaluate("AhKh", "QsQd", board="Th9h2c")
# → AKhh: 54.1% (flush + straight draw!)

# Hand vs range
result = calc.evaluate("AsKs", "QQ+,AKs", iterations=20000)

# 3-way pot
result = calc.evaluate("AhKh", "QsQd", "JcTc", iterations=20000)
```

### 3. Hand Range System

Parse, display, and manipulate standard poker range notation.

```python
from lisaloop.equity import RangeParser

parser = RangeParser()
r = parser.parse("QQ+,AKs,ATs+")

print(r)              # Range(40 combos, 3.0% of hands)
print(r.grid())       # 13x13 visual grid

# Check specific hands
r.contains("AhKh")   # True
r.contains("9h8h")   # False

# Combine or subtract ranges
wide = parser.parse("22+,ATs+,KJs+,QTs+,JTs,T9s,98s")
tight = parser.parse("QQ+,AK")
bluffs = wide.remove(tight)
```

### 4. Strategic Bet Sizing

Pot-geometric sizing, value sizing, bluff sizing, overbets.

```python
from lisaloop.strategy import BetSizer, SizingContext
from lisaloop.core.state import Street

sizer = BetSizer()
ctx = SizingContext(pot=100, stack=500, street=Street.FLOP, streets_remaining=3)

sizer.geometric(ctx)               # $61.80 — sets up all-in by river
sizer.value_size(ctx, 0.85)        # $67.50 — max extraction
sizer.bluff_size(ctx)              # $33.00 — minimize risk
sizer.overbet(ctx, multiplier=1.5) # $150.00 — pressure capped ranges

sizer.three_bet_size(6.0, in_position=True)   # $18.00
sizer.four_bet_size(18.0)                      # $40.50
```

### 5. Position Opening Charts

GTO-approximation opening ranges for every 6-max position.

```python
from lisaloop.strategy import PositionCharts

charts = PositionCharts()
charts.should_open("UTG", "ATs")  # True
charts.should_open("UTG", "87s")  # False
charts.should_open("BTN", "87s")  # True

charts.display("BTN")  # Visual 13x13 grid
```

### 6. ICM Tournament Equity

Independent Chip Model for tournament decisions.

```python
from lisaloop.strategy import ICMCalculator

icm = ICMCalculator()

stacks = [5000, 3000, 2000]
payouts = [50, 30, 20]
equities = icm.calculate(stacks, payouts)
# → [42.3%, 30.8%, 26.9%]

# Should you call an all-in?
ev = icm.decision_ev(stacks, payouts, hero=0,
    win_stacks=[7000, 3000, 0],
    lose_stacks=[3000, 3000, 4000],
    win_prob=0.60)

# Bubble factor
bf = icm.bubble_factor(stacks, payouts, hero=0, villain=2, pot=2000)
# → 1.4x (need 70% equity instead of 50%)
```

### 7. Hand History Replay

Replay any hand with ASCII card art, action-by-action breakdown.

```python
from lisaloop.replay import HandReplay

biggest_pot = max(result.hand_results, key=lambda h: h.pot_total)
replay = HandReplay(biggest_pot)
replay.show()
```

```
  ╔════════════════════════════════════════════════════════════════╗
  ║                        HAND REPLAY                           ║
  ║                         Hand #847                            ║
  ╚════════════════════════════════════════════════════════════════╝

  Board:
    ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
    │ T♠ │ │ 9♥ │ │ 2♦ │ │ K♣ │ │ 7♠ │
    └────┘ └────┘ └────┘ └────┘ └────┘

  ── PREFLOP ──────────────────────────────────────────────
    Lisa             raises to $1.25         (pot: $1.75)
    TAGBot           calls $1.25             (pot: $3.00)
    LAGBot           folds                   (pot: $3.00)

  ── FLOP ─────────────────────────────────────────────────
    Lisa             bets $2.10              (pot: $5.10)
    TAGBot           calls $2.10             (pot: $7.20)

  ── SHOWDOWN ─────────────────────────────────────────────
    Seat 0: [A♠ K♥]    Top Pair        ← WINNER
    Seat 1: [Q♣ J♦]    Straight Draw
```

### 8. Post-Match Analytics

```python
from lisaloop.analysis.stats import analyze_match, compare_agents

report = analyze_match(result)
for name, pr in report.player_reports.items():
    print(f"{name}: {pr.style} | {pr.bb_per_100:+.1f} BB/100 | Sharpe: {pr.sharpe_ratio:.2f}")

h2h = compare_agents(result, "Lisa", "SharkBot")
print(f"Edge: {h2h.edge_bb_per_100:+.1f} BB/100 ({h2h.confidence})")
```

### 9. Opponent Modeling

```python
from lisaloop.agents.lisa_agent import LisaAgent

lisa = LisaAgent()
# After running hands:
for name, model in lisa._opponents.items():
    print(f"{name}: {model.summary()} | VPIP: {model.vpip_pct:.0%} | AF: {model.aggression_factor:.1f}")
```

### 10. Webhook / Event System

```python
class TrackerAgent(Agent):
    name = "TrackerBot"

    def on_hand_end(self, result):
        requests.post(WEBHOOK_URL, json=result)

    def on_opponent_action(self, player_name, action, street):
        update_database(player_name, action, street)
```

---

<h2 id="cli-tools">CLI Tools</h2>

Every tool available in code is also available from the terminal.

```bash
# Tournament
lisaloop arena --hands 10000 --agents lisa,tag,lag,gto,random --analyze

# Quick 1v1
lisaloop quickplay --hands 5000

# Benchmark your agent
lisaloop benchmark my_agent.py --hands 10000

# Equity calculator
lisaloop equity AhKh QsQd
lisaloop equity AhKh QsQd --board Th9h2c --iterations 50000

# Range analysis
lisaloop range "QQ+,AKs,ATs+"

# Position charts
lisaloop charts BTN

# Hand replay
lisaloop replay --hands 100 --agents lisa,tag,lag --top 5

# Custom agents
lisaloop arena --agents lisa,my_agent.py,tag --hands 5000
```

---

<h2 id="api-reference">API Reference</h2>

### Game State

```python
state.my_hand           # Hand([A♠, K♥])
state.my_stack          # 485.0
state.board             # [T♠, 9♣, 2♦]
state.street            # Street.FLOP
state.pot.total         # 150.0
state.current_bet       # 50.0
state.valid_actions     # [FOLD, CALL $50.00, RAISE $100.00]
state.can_check()       # True/False
state.can_raise()       # True/False
state.position          # 2 (0=SB, 1=BB, 2=UTG, ...)
state.num_players       # 6
state.is_heads_up       # False
state.pot_odds          # 0.25
state.stack_to_pot_ratio # 3.2
state.history           # all actions this hand
state.to_dict()         # JSON-friendly dict
```

### Actions

```python
Action.fold()              # Give up
Action.check()             # Pass
Action.call(amount)        # Match current bet
Action.bet(amount)         # Open bet
Action.raise_to(amount)    # Raise to total
Action.all_in(amount)      # Ship it
```

Invalid actions auto-correct. Your agent can't break the game.

---

## Built-in Agents

| Agent | Style | VPIP | Strategy |
|-------|-------|------|----------|
| **Lisa** | Adaptive | ~24% | Opponent modeling, exploitative play, dynamic bluffs, board texture reads |
| **TAGBot** | Tight-Aggressive | ~20% | Premium hands, c-bet, fit-or-fold |
| **LAGBot** | Loose-Aggressive | ~35% | Wide range, constant pressure, high bluff frequency |
| **GTOBot** | Balanced | ~22% | Mixed strategies, pot-geometric sizing, MDF |
| **RandomBot** | Chaotic | ~50% | Random actions. If you lose to this, go home |

---

## Project Structure

```
lisaloop-sdk/
├── lisaloop/
│   ├── core/                     # Game engine
│   │   ├── cards.py              # Card, Hand, Deck, HandEvaluator
│   │   ├── state.py              # GameState, Action, PlayerState
│   │   └── table.py              # Full poker table simulation
│   ├── agents/                   # AI agents
│   │   ├── base.py               # Agent base class — subclass this
│   │   ├── lisa_agent.py         # Lisa — adaptive exploitative
│   │   ├── tag_agent.py          # Tight-Aggressive
│   │   ├── lag_agent.py          # Loose-Aggressive
│   │   ├── gto_agent.py          # GTO approximation
│   │   └── random_agent.py       # Random baseline
│   ├── equity/                   # Equity tools
│   │   ├── calculator.py         # Monte Carlo equity calculator
│   │   └── ranges.py             # Hand range parser + grid display
│   ├── strategy/                 # Strategy tools
│   │   ├── sizing.py             # Bet sizing (geometric, value, bluff)
│   │   ├── position.py           # 6-max opening charts
│   │   └── icm.py                # ICM calculator + bubble factor
│   ├── replay/                   # Hand replay
│   │   └── viewer.py             # ASCII hand history viewer
│   ├── arena/                    # Tournament engine
│   │   └── engine.py             # Arena, leaderboard, stats
│   ├── analysis/                 # Analytics
│   │   └── stats.py              # Match reports, H2H, Sharpe, drawdown
│   ├── examples/                 # Example code
│   │   ├── quickstart.py         # 10-line demo
│   │   ├── my_first_agent.py     # Starter template
│   │   ├── equity_demo.py        # Equity calculator walkthrough
│   │   ├── strategy_demo.py      # Sizing + ICM + charts demo
│   │   └── replay_demo.py        # Hand replay demo
│   └── cli.py                    # Full CLI
├── tests/
├── CONTRIBUTING.md
├── pyproject.toml
└── README.md
```

---

<h2 id="hackathon">Hackathon Tracks</h2>

| Track | Challenge | Difficulty |
|-------|-----------|------------|
| **Beat Lisa** | Build an agent that profits against Lisa over 10k hands | Hard |
| **Survival Mode** | $100 API credits, last agent standing wins | Medium |
| **Read the Table** | Best opponent modeling / profiling system | Hard |
| **Coach Lisa** | Best post-session analysis or coaching tool | Medium |
| **Dashboard** | Best real-time visualization or monitoring | Medium |
| **Range Warrior** | Best preflop range construction tool | Easy |
| **New Game** | Adapt for Omaha, Short Deck, or tournaments | Hard |
| **Wild Card** | Surprise us | ??? |

---

## Configuration

```python
ArenaConfig(
    hands=10000,           # Total hands
    table_size=6,          # 2-6 players
    small_blind=0.25,
    big_blind=0.50,
    starting_stack=100.0,  # 200BB deep
    seed=42,               # Reproducible
    rebuy=True,
    rebuy_threshold=20.0,
    verbose=True,
    log_interval=100,
)
```

---

## Lisa's Live Stats

| Metric | Value |
|--------|-------|
| Net Profit | +$135.50 |
| Hands Played | 12,847+ |
| Winrate | +6.8 BB/100 |
| VPIP / PFR | 24.1% / 18.7% |
| Aggression Factor | 2.4x |
| Stakes | NL50 ($0.25/$0.50) |
| Hardware | Mac Mini M4, 16GB |
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
