"""
Plugin base class — the extension point for the Lisa Loop framework.

Every plugin implements a contract: a name, version, type, and lifecycle
hooks. Plugins can provide agents, evaluators, providers, actions,
or services to the runtime.

Usage:
    from lisaloop.plugins import Plugin, PluginType

    class MyPlugin(Plugin):
        name = "my-plugin"
        version = "1.0"
        type = PluginType.AGENT

        def initialize(self, runtime):
            # Called when the runtime loads this plugin
            self.register_agent(MyCustomAgent)

        def shutdown(self):
            # Called when the runtime is shutting down
            pass
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from lisaloop.runtime.core import AgentRuntime


class PluginType(Enum):
    """Types of plugins the framework supports."""
    AGENT = "agent"
    EVALUATOR = "evaluator"
    PROVIDER = "provider"
    ACTION = "action"
    SERVICE = "service"
    ENVIRONMENT = "environment"
    MEMORY = "memory"
    MIDDLEWARE = "middleware"


class Plugin(ABC):
    """
    Base class for all Lisa Loop plugins.

    A plugin is a self-contained extension that adds functionality
    to the framework. Plugins are loaded by the runtime and can
    register agents, evaluators, providers, and services.

    Lifecycle:
        1. Plugin is discovered (file scan or explicit registration)
        2. initialize(runtime) is called — register your components
        3. Plugin is active and participates in the framework
        4. shutdown() is called on runtime exit
    """

    name: str = "unnamed-plugin"
    version: str = "0.1"
    description: str = ""
    author: str = ""
    type: PluginType = PluginType.AGENT

    # Dependencies: list of plugin names this plugin requires
    dependencies: List[str] = []

    def __init__(self):
        self._runtime: Optional[AgentRuntime] = None
        self._initialized = False
        self._config: Dict[str, Any] = {}

    @abstractmethod
    def initialize(self, runtime: AgentRuntime) -> None:
        """
        Called when the runtime loads this plugin.

        Use this to register agents, evaluators, providers, etc.
        The runtime reference lets you access other framework services.
        """
        ...

    def shutdown(self) -> None:
        """Called when the runtime is shutting down. Cleanup here."""
        pass

    def configure(self, config: Dict[str, Any]) -> None:
        """Apply configuration to this plugin."""
        self._config = config

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def __repr__(self) -> str:
        status = "active" if self._initialized else "inactive"
        return f"<Plugin:{self.name} v{self.version} [{self.type.value}] ({status})>"
