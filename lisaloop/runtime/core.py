"""
AgentRuntime — the central orchestrator of the Lisa Loop framework.

The runtime manages the full lifecycle: plugin loading, agent registration,
event dispatch, memory persistence, provider injection, and game execution.

This is the entry point for building anything with Lisa Loop.

Usage:
    from lisaloop.runtime import AgentRuntime, RuntimeConfig

    # Create runtime
    runtime = AgentRuntime(RuntimeConfig(
        name="my-session",
        seed=42,
        verbose=True,
    ))

    # Load plugins
    runtime.load_plugin(MyPlugin())

    # Register agents
    runtime.register_agent(LisaAgent(seed=42))
    runtime.register_agent(TAGAgent(seed=42))

    # Run
    result = runtime.run_arena(hands=10000)

    # Or start a persistent session
    runtime.start()
    runtime.run_hand()
    runtime.run_hand()
    runtime.stop()
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from lisaloop.agents.base import Agent
from lisaloop.events.bus import EventBus, Event, EventType
from lisaloop.plugins.base import Plugin
from lisaloop.plugins.registry import PluginRegistry
from lisaloop.plugins.loader import PluginLoader

logger = logging.getLogger("lisaloop.runtime")


@dataclass
class RuntimeConfig:
    """Configuration for the AgentRuntime."""
    name: str = "lisa-runtime"
    seed: int | None = None
    verbose: bool = True

    # Table settings
    table_size: int = 6
    small_blind: float = 0.25
    big_blind: float = 0.50
    starting_stack: float = 100.0

    # Memory
    memory_enabled: bool = True
    memory_path: str = "lisa_memory.db"

    # Plugin directory
    plugin_dir: str | None = None

    # Logging
    log_level: str = "INFO"


class AgentRuntime:
    """
    Central orchestrator for the Lisa Loop framework.

    Manages:
    - Plugin lifecycle (load, initialize, shutdown)
    - Agent registration and management
    - Event bus for framework-wide communication
    - Provider registration for context injection
    - Memory/persistence coordination
    - Game execution (single hands, tournaments, training)

    This is the "brain" that ties everything together.
    """

    def __init__(self, config: RuntimeConfig | None = None):
        self.config = config or RuntimeConfig()
        self.events = EventBus()
        self.plugins = PluginRegistry()
        self._loader = PluginLoader()

        self._agents: List[Agent] = []
        self._providers: Dict[str, Any] = {}
        self._middleware: List[Callable] = []
        self._services: Dict[str, Any] = {}
        self._state: Dict[str, Any] = {}

        self._running = False
        self._start_time: Optional[float] = None
        self._hands_played = 0

        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper(), logging.INFO),
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%H:%M:%S",
        )

    # ── Plugin Management ────────────────────────────────

    def load_plugin(self, plugin: Plugin) -> None:
        """Register and initialize a plugin."""
        self.plugins.register(plugin)
        self.events.emit(Event(
            EventType.PLUGIN_LOADED,
            data={"plugin": plugin.name, "version": plugin.version},
            source="runtime",
        ))

    def load_plugins_from_directory(self, directory: str) -> int:
        """Discover and load all plugins from a directory."""
        plugins = self._loader.load_directory(directory)
        for p in plugins:
            self.load_plugin(p)
        return len(plugins)

    def load_plugins_from_file(self, path: str) -> int:
        """Load plugins from a single Python file."""
        plugins = self._loader.load_file(path)
        for p in plugins:
            self.load_plugin(p)
        return len(plugins)

    # ── Agent Management ─────────────────────────────────

    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the runtime."""
        self._agents.append(agent)
        self.events.emit(Event(
            EventType.AGENT_REGISTERED,
            data={"agent": agent.name, "version": agent.version},
            source="runtime",
        ))
        logger.info(f"Registered agent: {agent.name} v{agent.version}")

    def get_agent(self, name: str) -> Optional[Agent]:
        """Get a registered agent by name."""
        for a in self._agents:
            if a.name == name:
                return a
        return None

    @property
    def agents(self) -> List[Agent]:
        return list(self._agents)

    # ── Provider System ──────────────────────────────────

    def register_provider(self, name: str, provider: Any) -> None:
        """
        Register a context provider.

        Providers inject additional context into agent decisions.
        They can provide equity calculations, opponent stats,
        position information, or any other computed data.
        """
        self._providers[name] = provider
        logger.info(f"Registered provider: {name}")

    def get_provider(self, name: str) -> Optional[Any]:
        """Get a registered provider by name."""
        return self._providers.get(name)

    # ── Middleware ────────────────────────────────────────

    def use(self, middleware: Callable) -> None:
        """
        Add middleware to the action processing pipeline.

        Middleware functions receive (agent, state, action) and can
        modify, log, validate, or reject actions before they execute.
        """
        self._middleware.append(middleware)
        logger.info(f"Added middleware: {middleware.__name__}")

    # ── Service Registry ─────────────────────────────────

    def register_service(self, name: str, service: Any) -> None:
        """Register a shared service (database, API client, etc.)."""
        self._services[name] = service

    def get_service(self, name: str) -> Optional[Any]:
        """Get a registered service by name."""
        return self._services.get(name)

    # ── State ────────────────────────────────────────────

    def set_state(self, key: str, value: Any) -> None:
        """Set runtime state (shared across all components)."""
        self._state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get runtime state."""
        return self._state.get(key, default)

    # ── Lifecycle ────────────────────────────────────────

    def start(self) -> None:
        """
        Start the runtime.

        Initializes all plugins, sets up memory, and prepares
        the framework for game execution.
        """
        if self._running:
            logger.warning("Runtime is already running")
            return

        logger.info(f"Starting runtime: {self.config.name}")
        self._start_time = time.time()

        # Auto-load plugins from directory
        if self.config.plugin_dir:
            self.load_plugins_from_directory(self.config.plugin_dir)

        # Initialize all plugins
        self.plugins.initialize_all(self)

        # Initialize memory if enabled
        if self.config.memory_enabled:
            self._init_memory()

        self._running = True
        self.events.emit(Event(EventType.RUNTIME_START, source="runtime"))
        logger.info("Runtime started")

    def stop(self) -> None:
        """Stop the runtime and cleanup."""
        if not self._running:
            return

        logger.info("Stopping runtime...")
        self.events.emit(Event(EventType.RUNTIME_STOP, source="runtime"))

        # Shutdown plugins in reverse order
        self.plugins.shutdown_all()

        self._running = False
        duration = time.time() - (self._start_time or time.time())
        logger.info(f"Runtime stopped. Duration: {duration:.1f}s, Hands: {self._hands_played}")

    # ── Game Execution ───────────────────────────────────

    def run_arena(self, hands: int = 1000, **kwargs) -> Any:
        """
        Run an arena tournament with all registered agents.

        This is the easiest way to run a match. It creates a table,
        seats all registered agents, runs the specified number of hands,
        and returns the full results.
        """
        from lisaloop.arena.engine import Arena, ArenaConfig

        config = ArenaConfig(
            hands=hands,
            table_size=kwargs.get("table_size", self.config.table_size),
            small_blind=kwargs.get("small_blind", self.config.small_blind),
            big_blind=kwargs.get("big_blind", self.config.big_blind),
            starting_stack=kwargs.get("starting_stack", self.config.starting_stack),
            seed=kwargs.get("seed", self.config.seed),
            verbose=kwargs.get("verbose", self.config.verbose),
        )

        arena = Arena(config)
        for agent in self._agents:
            arena.register(agent)

        self.events.emit_simple(EventType.TOURNAMENT_START, source="runtime", hands=hands)

        was_running = self._running
        if not was_running:
            self.start()

        result = arena.run()
        self._hands_played += result.hands_played

        self.events.emit(Event(
            EventType.TOURNAMENT_END,
            data={
                "hands_played": result.hands_played,
                "winner": result.winner.name,
                "winner_profit": result.winner.total_profit,
            },
            source="runtime",
        ))

        if not was_running:
            self.stop()

        return result

    def run_table(self, hands: int = 1) -> List[Any]:
        """Run hands on a table with registered agents. Returns HandResults."""
        from lisaloop.core.table import Table, TableConfig

        table = Table(TableConfig(
            num_seats=self.config.table_size,
            small_blind=self.config.small_blind,
            big_blind=self.config.big_blind,
            seed=self.config.seed,
        ))

        for i, agent in enumerate(self._agents):
            table.seat_player(i, agent, name=agent.name, stack=self.config.starting_stack)

        results = []
        for _ in range(hands):
            result = table.play_hand()
            results.append(result)

            self.events.emit(Event(
                EventType.HAND_COMPLETE,
                data={
                    "hand_number": result.hand_number,
                    "pot": result.pot_total,
                    "winners": list(result.winners.keys()),
                },
                source="runtime",
            ))

        self._hands_played += len(results)
        return results

    # ── Memory ───────────────────────────────────────────

    def _init_memory(self) -> None:
        """Initialize the memory system."""
        try:
            from lisaloop.memory.store import MemoryStore
            store = MemoryStore(self.config.memory_path)
            self.register_service("memory", store)
            logger.info(f"Memory initialized: {self.config.memory_path}")
        except ImportError:
            logger.debug("Memory module not available")

    # ── Info ─────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def uptime(self) -> float:
        if not self._start_time:
            return 0.0
        return time.time() - self._start_time

    def status(self) -> Dict[str, Any]:
        """Get runtime status summary."""
        return {
            "name": self.config.name,
            "running": self._running,
            "uptime": self.uptime,
            "agents": [a.name for a in self._agents],
            "plugins": self.plugins.names,
            "providers": list(self._providers.keys()),
            "services": list(self._services.keys()),
            "middleware": len(self._middleware),
            "hands_played": self._hands_played,
            "events_emitted": self.events.event_count,
        }

    def __repr__(self) -> str:
        status = "running" if self._running else "stopped"
        return (
            f"AgentRuntime('{self.config.name}', {status}, "
            f"{len(self._agents)} agents, {len(self.plugins)} plugins)"
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
