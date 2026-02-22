"""
Event bus — pub/sub system for framework-wide communication.

Any component can publish events and any component can subscribe.
Events flow through the system without tight coupling.

Usage:
    from lisaloop.events import EventBus, Event, EventType

    bus = EventBus()

    # Subscribe to events
    def on_hand_complete(event):
        print(f"Hand #{event.data['hand_number']} complete!")

    bus.on(EventType.HAND_COMPLETE, on_hand_complete)

    # Publish events
    bus.emit(Event(EventType.HAND_COMPLETE, data={"hand_number": 42}))

    # One-time listener
    bus.once(EventType.TOURNAMENT_END, lambda e: print("Tournament over!"))

    # Wildcard listener (all events)
    bus.on("*", lambda e: log(e))
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("lisaloop.events")


class EventType(Enum):
    """Built-in event types. Plugins can define custom types as strings."""

    # Runtime lifecycle
    RUNTIME_START = "runtime.start"
    RUNTIME_STOP = "runtime.stop"
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_ERROR = "plugin.error"

    # Game events
    HAND_START = "hand.start"
    HAND_COMPLETE = "hand.complete"
    STREET_CHANGE = "street.change"
    ACTION_TAKEN = "action.taken"
    SHOWDOWN = "showdown"
    POT_AWARDED = "pot.awarded"

    # Agent events
    AGENT_REGISTERED = "agent.registered"
    AGENT_DECISION = "agent.decision"
    AGENT_ERROR = "agent.error"

    # Tournament events
    TOURNAMENT_START = "tournament.start"
    TOURNAMENT_END = "tournament.end"
    MATCH_COMPLETE = "match.complete"
    LEADERBOARD_UPDATE = "leaderboard.update"

    # Memory events
    MEMORY_SAVE = "memory.save"
    MEMORY_LOAD = "memory.load"
    OPPONENT_UPDATE = "opponent.update"

    # Training events
    TRAINING_START = "training.start"
    TRAINING_EPOCH = "training.epoch"
    TRAINING_COMPLETE = "training.complete"


@dataclass
class Event:
    """An event that flows through the event bus."""
    type: EventType | str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: float = field(default_factory=time.time)

    @property
    def type_str(self) -> str:
        if isinstance(self.type, EventType):
            return self.type.value
        return self.type

    def __repr__(self) -> str:
        return f"Event({self.type_str}, source={self.source!r})"


# Type for event handlers
EventHandler = Callable[[Event], None]


class EventBus:
    """
    Publish/subscribe event system.

    Features:
    - Type-safe event subscription
    - Wildcard listeners (subscribe to all events)
    - One-time listeners (auto-unsubscribe after first event)
    - Event history for debugging
    - Handler error isolation (one bad handler doesn't break others)
    """

    def __init__(self, history_size: int = 100):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._once_handlers: Dict[str, List[EventHandler]] = {}
        self._wildcard_handlers: List[EventHandler] = []
        self._history: List[Event] = []
        self._history_size = history_size
        self._event_count = 0

    def on(self, event_type: EventType | str, handler: EventHandler) -> None:
        """Subscribe to an event type."""
        key = self._key(event_type)
        if key == "*":
            self._wildcard_handlers.append(handler)
        else:
            if key not in self._handlers:
                self._handlers[key] = []
            self._handlers[key].append(handler)

    def once(self, event_type: EventType | str, handler: EventHandler) -> None:
        """Subscribe to an event type — handler fires once then auto-removes."""
        key = self._key(event_type)
        if key not in self._once_handlers:
            self._once_handlers[key] = []
        self._once_handlers[key].append(handler)

    def off(self, event_type: EventType | str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        key = self._key(event_type)
        if key == "*":
            self._wildcard_handlers = [h for h in self._wildcard_handlers if h != handler]
        elif key in self._handlers:
            self._handlers[key] = [h for h in self._handlers[key] if h != handler]

    def emit(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        key = self._key(event.type)
        self._event_count += 1

        # Record history
        self._history.append(event)
        if len(self._history) > self._history_size:
            self._history.pop(0)

        # Fire type-specific handlers
        for handler in self._handlers.get(key, []):
            self._safe_call(handler, event)

        # Fire one-time handlers
        once = self._once_handlers.pop(key, [])
        for handler in once:
            self._safe_call(handler, event)

        # Fire wildcard handlers
        for handler in self._wildcard_handlers:
            self._safe_call(handler, event)

    def emit_simple(self, event_type: EventType | str, source: str = "", **data) -> None:
        """Convenience: emit an event without constructing Event manually."""
        self.emit(Event(type=event_type, data=data, source=source))

    @property
    def history(self) -> List[Event]:
        """Recent event history for debugging."""
        return list(self._history)

    @property
    def event_count(self) -> int:
        """Total events emitted."""
        return self._event_count

    def clear(self) -> None:
        """Remove all handlers and history."""
        self._handlers.clear()
        self._once_handlers.clear()
        self._wildcard_handlers.clear()
        self._history.clear()
        self._event_count = 0

    def _key(self, event_type: EventType | str) -> str:
        if isinstance(event_type, EventType):
            return event_type.value
        return event_type

    def _safe_call(self, handler: EventHandler, event: Event) -> None:
        try:
            handler(event)
        except Exception as e:
            logger.error(f"Event handler error for {event.type_str}: {e}")

    def __repr__(self) -> str:
        total_handlers = sum(len(h) for h in self._handlers.values()) + len(self._wildcard_handlers)
        return f"EventBus({total_handlers} handlers, {self._event_count} events emitted)"
