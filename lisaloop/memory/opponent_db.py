"""
Opponent database — persistent opponent tracking across sessions.

Unlike in-memory OpponentModel, this persists to disk so Lisa
remembers every opponent she's ever played against.

Usage:
    from lisaloop.memory import OpponentDatabase

    db = OpponentDatabase("opponents.db")
    db.record(name="FishPlayer", vpip=True, pfr=False, aggression_action="call")

    profile = db.get_profile("FishPlayer")
    print(f"VPIP: {profile['vpip_pct']:.0%}")
    print(f"Type: {profile['classification']}")

    all_opponents = db.all_profiles()
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from typing import Dict, List, Optional

logger = logging.getLogger("lisaloop.memory.opponents")


class OpponentDatabase:
    """Persistent opponent tracking database."""

    def __init__(self, path: str = "opponents.db"):
        self._path = path
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS opponents (
                name TEXT PRIMARY KEY,
                hands_seen INTEGER DEFAULT 0,
                vpip INTEGER DEFAULT 0,
                pfr INTEGER DEFAULT 0,
                af_bets INTEGER DEFAULT 0,
                af_calls INTEGER DEFAULT 0,
                cbets INTEGER DEFAULT 0,
                cbet_opportunities INTEGER DEFAULT 0,
                fold_to_cbet INTEGER DEFAULT 0,
                fold_to_cbet_opportunities INTEGER DEFAULT 0,
                three_bets INTEGER DEFAULT 0,
                showdowns INTEGER DEFAULT 0,
                showdowns_won INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0,
                notes TEXT DEFAULT '[]',
                first_seen REAL,
                last_seen REAL
            );
        """)
        self._conn.commit()

    def record(
        self,
        name: str,
        vpip: bool = False,
        pfr: bool = False,
        aggression_action: str = "",  # "bet", "raise", "call", "fold"
        cbet: bool = False,
        cbet_opportunity: bool = False,
        fold_to_cbet: bool = False,
        fold_to_cbet_opportunity: bool = False,
        showdown: bool = False,
        showdown_won: bool = False,
        profit: float = 0.0,
    ) -> None:
        """Record a hand observation for an opponent."""
        now = time.time()

        # Ensure row exists
        self._conn.execute(
            "INSERT OR IGNORE INTO opponents (name, first_seen, last_seen) VALUES (?, ?, ?)",
            (name, now, now),
        )

        updates = ["hands_seen = hands_seen + 1", "last_seen = ?"]
        params = [now]

        if vpip:
            updates.append("vpip = vpip + 1")
        if pfr:
            updates.append("pfr = pfr + 1")
        if aggression_action in ("bet", "raise"):
            updates.append("af_bets = af_bets + 1")
        elif aggression_action == "call":
            updates.append("af_calls = af_calls + 1")
        if cbet:
            updates.append("cbets = cbets + 1")
        if cbet_opportunity:
            updates.append("cbet_opportunities = cbet_opportunities + 1")
        if fold_to_cbet:
            updates.append("fold_to_cbet = fold_to_cbet + 1")
        if fold_to_cbet_opportunity:
            updates.append("fold_to_cbet_opportunities = fold_to_cbet_opportunities + 1")
        if showdown:
            updates.append("showdowns = showdowns + 1")
        if showdown_won:
            updates.append("showdowns_won = showdowns_won + 1")
        if profit != 0:
            updates.append(f"total_profit = total_profit + {profit}")

        query = f"UPDATE opponents SET {', '.join(updates)} WHERE name = ?"
        params.append(name)
        self._conn.execute(query, params)
        self._conn.commit()

    def get_profile(self, name: str) -> Optional[Dict]:
        """Get full profile for an opponent."""
        row = self._conn.execute(
            "SELECT * FROM opponents WHERE name = ?", (name,)
        ).fetchone()

        if not row:
            return None

        d = dict(row)
        hands = max(1, d["hands_seen"])

        d["vpip_pct"] = d["vpip"] / hands
        d["pfr_pct"] = d["pfr"] / hands
        d["aggression_factor"] = d["af_bets"] / max(1, d["af_calls"])
        d["cbet_pct"] = d["cbets"] / max(1, d["cbet_opportunities"])
        d["fold_to_cbet_pct"] = d["fold_to_cbet"] / max(1, d["fold_to_cbet_opportunities"])
        d["showdown_win_pct"] = d["showdowns_won"] / max(1, d["showdowns"])
        d["classification"] = self._classify(d)

        return d

    def all_profiles(self) -> List[Dict]:
        """Get all opponent profiles."""
        rows = self._conn.execute(
            "SELECT name FROM opponents ORDER BY hands_seen DESC"
        ).fetchall()
        return [self.get_profile(r["name"]) for r in rows]

    def add_note(self, name: str, note: str) -> None:
        """Add a note about an opponent."""
        row = self._conn.execute(
            "SELECT notes FROM opponents WHERE name = ?", (name,)
        ).fetchone()
        if row:
            notes = json.loads(row["notes"])
            notes.append({"text": note, "time": time.time()})
            self._conn.execute(
                "UPDATE opponents SET notes = ? WHERE name = ?",
                (json.dumps(notes), name),
            )
            self._conn.commit()

    def get_notes(self, name: str) -> List[Dict]:
        """Get all notes for an opponent."""
        row = self._conn.execute(
            "SELECT notes FROM opponents WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return json.loads(row["notes"])
        return []

    def _classify(self, profile: Dict) -> str:
        vpip = profile["vpip_pct"]
        pfr = profile["pfr_pct"]
        af = profile["aggression_factor"]

        if profile["hands_seen"] < 20:
            return "Unknown"
        if vpip > 0.40:
            return "Fish" if af < 1.5 else "Maniac"
        if vpip < 0.15:
            return "Nit"
        if vpip > 0.28 and af > 2.0:
            return "LAG"
        if vpip < 0.24 and pfr > 0.16:
            return "TAG"
        if vpip > 0.35 and pfr < 0.15:
            return "Calling Station"
        return "Regular"

    @property
    def total_opponents(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as cnt FROM opponents").fetchone()
        return row["cnt"]

    def close(self) -> None:
        self._conn.close()

    def __repr__(self) -> str:
        return f"OpponentDatabase('{self._path}', {self.total_opponents} opponents)"
