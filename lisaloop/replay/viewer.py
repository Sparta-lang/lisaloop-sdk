"""
Hand history replay with rich ASCII visualization.

Replay any hand from arena results with a beautiful step-by-step
visualization of all actions, board cards, pot sizes, and outcomes.

Usage:
    from lisaloop.replay import HandReplay

    replay = HandReplay(result.hand_results[0])
    replay.show()            # Full hand replay
    replay.show_summary()    # Compact one-line summary
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, TextIO, Tuple

from lisaloop.core.cards import Card, Hand
from lisaloop.core.state import ActionRecord, ActionType, Street
from lisaloop.core.table import HandResult


STREET_NAMES = {
    Street.PREFLOP: "PREFLOP",
    Street.FLOP: "FLOP",
    Street.TURN: "TURN",
    Street.RIVER: "RIVER",
}

CARD_ART = {
    "top":    "┌───┐",
    "mid":    "│ {} │",
    "bottom": "└───┘",
}

SUITS_COLOR = {"♠": "♠", "♥": "♥", "♦": "♦", "♣": "♣"}


def _card_lines(cards: List[Card]) -> List[str]:
    """Render cards as ASCII art lines."""
    if not cards:
        return ["", "  [no cards]", ""]

    tops = []
    mids = []
    bots = []
    for c in cards:
        symbol = f"{c.rank.symbol}{c.suit.symbol}"
        tops.append("┌────┐")
        mids.append(f"│ {symbol:<2} │")
        bots.append("└────┘")

    return [
        " ".join(tops),
        " ".join(mids),
        " ".join(bots),
    ]


class HandReplay:
    """
    Rich hand history viewer.

    Renders a complete hand replay with ASCII card art, pot tracking,
    action-by-action breakdown, and outcome summary.
    """

    def __init__(self, hand_result: HandResult):
        self.result = hand_result

    def show(self, out: TextIO | None = None) -> str:
        """Render full hand replay. Returns string and optionally writes to stream."""
        out = out or sys.stdout
        lines = []

        # Header
        lines.append("")
        lines.append(f"  ╔{'═' * 60}╗")
        lines.append(f"  ║{'HAND REPLAY':^60}║")
        lines.append(f"  ║{f'Hand #{self.result.hand_number}':^60}║")
        lines.append(f"  ╚{'═' * 60}╝")
        lines.append("")

        # Board
        if self.result.board:
            lines.append("  Board:")
            for line in _card_lines(self.result.board):
                lines.append(f"    {line}")
            lines.append("")

        # Group actions by street
        streets: Dict[Street, List[ActionRecord]] = {}
        for record in self.result.history:
            if record.street not in streets:
                streets[record.street] = []
            streets[record.street].append(record)

        # Show each street
        for street in [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER]:
            if street not in streets:
                continue

            street_name = STREET_NAMES.get(street, str(street))
            lines.append(f"  ── {street_name} {'─' * (52 - len(street_name))}")

            # Show board at this street
            if street == Street.FLOP and len(self.result.board) >= 3:
                for line in _card_lines(self.result.board[:3]):
                    lines.append(f"    {line}")
            elif street == Street.TURN and len(self.result.board) >= 4:
                for line in _card_lines(self.result.board[:4]):
                    lines.append(f"    {line}")
            elif street == Street.RIVER and len(self.result.board) >= 5:
                for line in _card_lines(self.result.board[:5]):
                    lines.append(f"    {line}")

            lines.append("")

            for record in streets[street]:
                action_str = self._format_action(record)
                pot_str = f"(pot: ${record.pot_after:.2f})"
                lines.append(f"    {record.player_name:<16} {action_str:<24} {pot_str}")

            lines.append("")

        # Showdown
        if self.result.showdown:
            lines.append(f"  ── SHOWDOWN {'─' * 44}")
            lines.append("")
            for seat, (hand, rank_name) in self.result.showdown.items():
                won = seat in self.result.winners
                marker = " ← WINNER" if won else ""
                hand_str = f"[{hand.cards[0]!r} {hand.cards[1]!r}]"
                lines.append(f"    Seat {seat}: {hand_str:<16} {rank_name}{marker}")
            lines.append("")

        # Results
        lines.append(f"  ── RESULT {'─' * 47}")
        lines.append("")
        total_pot = self.result.pot_total
        lines.append(f"    Pot: ${total_pot:.2f}")
        for seat, amount in self.result.winners.items():
            lines.append(f"    Seat {seat} wins ${amount:.2f}")
        lines.append("")
        lines.append(f"  {'─' * 62}")

        text = "\n".join(lines)
        out.write(text + "\n")
        return text

    def show_summary(self, out: TextIO | None = None) -> str:
        """One-line summary of the hand."""
        out = out or sys.stdout
        winners = ", ".join(f"Seat {s}" for s in self.result.winners)
        amounts = sum(self.result.winners.values())
        board = " ".join(repr(c) for c in self.result.board) if self.result.board else "—"
        text = f"Hand #{self.result.hand_number}: Pot ${self.result.pot_total:.2f} → {winners} (${amounts:.2f}) | Board: {board}"
        out.write(text + "\n")
        return text

    def _format_action(self, record: ActionRecord) -> str:
        action = record.action
        if action.type == ActionType.FOLD:
            return "folds"
        elif action.type == ActionType.CHECK:
            return "checks"
        elif action.type == ActionType.CALL:
            return f"calls ${action.amount:.2f}"
        elif action.type == ActionType.BET:
            return f"bets ${action.amount:.2f}"
        elif action.type == ActionType.RAISE:
            return f"raises to ${action.amount:.2f}"
        elif action.type == ActionType.ALL_IN:
            return f"ALL-IN ${action.amount:.2f}"
        return str(action)
