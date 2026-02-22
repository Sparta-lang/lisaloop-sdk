"""
Memory store — persistent storage with SQLite backend.

Agents and plugins can save/load data that persists across sessions.
Supports hand histories, opponent models, agent state, and arbitrary
key-value data.

Usage:
    from lisaloop.memory import MemoryStore

    store = MemoryStore("lisa_memory.db")

    # Key-value storage
    store.set("last_session", {"hands": 5000, "profit": 42.50})
    data = store.get("last_session")

    # Hand history
    store.save_hand(hand_result)
    history = store.get_hands(limit=100)

    # Agent state persistence
    store.save_agent_state("Lisa", {"opponents": {...}, "total_hands": 50000})
    state = store.load_agent_state("Lisa")
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("lisaloop.memory")


class MemoryStore:
    """
    SQLite-backed persistent memory for the framework.

    Tables:
    - kv_store: Generic key-value storage
    - hand_history: Recorded hand results
    - agent_state: Persistent agent state
    - facts: Named facts/knowledge entries
    """

    def __init__(self, path: str = "lisa_memory.db"):
        self._path = path
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()
        logger.info(f"Memory store initialized: {path}")

    def _init_tables(self) -> None:
        c = self._conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hand_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hand_number INTEGER,
                pot_total REAL,
                winners TEXT,
                board TEXT,
                history TEXT,
                recorded_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_state (
                agent_name TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT DEFAULT '',
                created_at REAL NOT NULL,
                UNIQUE(category, key)
            );
        """)
        self._conn.commit()

    # ── Key-Value Store ──────────────────────────────

    def set(self, key: str, value: Any) -> None:
        """Set a key-value pair."""
        self._conn.execute(
            "INSERT OR REPLACE INTO kv_store (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), time.time()),
        )
        self._conn.commit()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key."""
        row = self._conn.execute(
            "SELECT value FROM kv_store WHERE key = ?", (key,)
        ).fetchone()
        if row:
            return json.loads(row["value"])
        return default

    def delete(self, key: str) -> None:
        """Delete a key-value pair."""
        self._conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
        self._conn.commit()

    def keys(self, prefix: str = "") -> List[str]:
        """List all keys, optionally filtered by prefix."""
        if prefix:
            rows = self._conn.execute(
                "SELECT key FROM kv_store WHERE key LIKE ?", (f"{prefix}%",)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT key FROM kv_store").fetchall()
        return [r["key"] for r in rows]

    # ── Hand History ─────────────────────────────────

    def save_hand(self, hand_result: Any) -> None:
        """Save a hand result to history."""
        self._conn.execute(
            "INSERT INTO hand_history (hand_number, pot_total, winners, board, history, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                hand_result.hand_number,
                hand_result.pot_total,
                json.dumps({str(k): v for k, v in hand_result.winners.items()}),
                json.dumps([str(c) for c in hand_result.board]),
                json.dumps([
                    {
                        "player": r.player_name,
                        "action": r.action.type.value,
                        "amount": r.action.amount,
                        "street": r.street.value,
                    }
                    for r in hand_result.history
                ]),
                time.time(),
            ),
        )
        self._conn.commit()

    def get_hands(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Retrieve hand history entries."""
        rows = self._conn.execute(
            "SELECT * FROM hand_history ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    @property
    def total_hands(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as cnt FROM hand_history").fetchone()
        return row["cnt"]

    # ── Agent State ──────────────────────────────────

    def save_agent_state(self, agent_name: str, state: Dict) -> None:
        """Save persistent agent state."""
        self._conn.execute(
            "INSERT OR REPLACE INTO agent_state (agent_name, state, updated_at) VALUES (?, ?, ?)",
            (agent_name, json.dumps(state), time.time()),
        )
        self._conn.commit()

    def load_agent_state(self, agent_name: str) -> Optional[Dict]:
        """Load persistent agent state."""
        row = self._conn.execute(
            "SELECT state FROM agent_state WHERE agent_name = ?", (agent_name,)
        ).fetchone()
        if row:
            return json.loads(row["state"])
        return None

    # ── Facts / Knowledge ────────────────────────────

    def add_fact(self, category: str, key: str, value: str, source: str = "") -> None:
        """Add a fact/knowledge entry."""
        self._conn.execute(
            "INSERT OR REPLACE INTO facts (category, key, value, source, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (category, key, value, source, time.time()),
        )
        self._conn.commit()

    def get_facts(self, category: str) -> List[Dict]:
        """Get all facts in a category."""
        rows = self._conn.execute(
            "SELECT * FROM facts WHERE category = ? ORDER BY created_at DESC",
            (category,),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_facts(self, query: str) -> List[Dict]:
        """Search facts by key or value."""
        rows = self._conn.execute(
            "SELECT * FROM facts WHERE key LIKE ? OR value LIKE ?",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Lifecycle ────────────────────────────────────

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    @property
    def path(self) -> str:
        return self._path

    def __repr__(self) -> str:
        return f"MemoryStore('{self._path}', {self.total_hands} hands)"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
