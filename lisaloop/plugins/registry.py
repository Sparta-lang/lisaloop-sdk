"""
Plugin registry — central catalog of all loaded plugins.

The registry manages plugin discovery, dependency resolution,
initialization ordering, and lifecycle management.

Usage:
    from lisaloop.plugins import PluginRegistry

    registry = PluginRegistry()
    registry.register(MyPlugin())
    registry.register(AnotherPlugin())

    # Initialize all plugins in dependency order
    registry.initialize_all(runtime)

    # Query plugins
    agents = registry.get_by_type(PluginType.AGENT)
    my_plugin = registry.get("my-plugin")
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, TYPE_CHECKING

from lisaloop.plugins.base import Plugin, PluginType

if TYPE_CHECKING:
    from lisaloop.runtime.core import AgentRuntime

logger = logging.getLogger("lisaloop.plugins")


class PluginRegistry:
    """
    Central registry for all framework plugins.

    Handles:
    - Plugin registration and deregistration
    - Dependency resolution and initialization ordering
    - Type-based plugin queries
    - Lifecycle management (init, shutdown)
    """

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._init_order: List[str] = []

    def register(self, plugin: Plugin) -> None:
        """Register a plugin. Does not initialize it yet."""
        if plugin.name in self._plugins:
            logger.warning(f"Plugin '{plugin.name}' already registered. Replacing.")
        self._plugins[plugin.name] = plugin
        logger.info(f"Registered plugin: {plugin}")

    def unregister(self, name: str) -> None:
        """Remove a plugin from the registry."""
        if name in self._plugins:
            plugin = self._plugins[name]
            if plugin.is_initialized:
                plugin.shutdown()
                plugin._initialized = False
            del self._plugins[name]
            logger.info(f"Unregistered plugin: {name}")

    def get(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def get_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Get all plugins of a specific type."""
        return [p for p in self._plugins.values() if p.type == plugin_type]

    @property
    def all_plugins(self) -> List[Plugin]:
        return list(self._plugins.values())

    @property
    def names(self) -> List[str]:
        return list(self._plugins.keys())

    def initialize_all(self, runtime: AgentRuntime) -> None:
        """
        Initialize all plugins in dependency order.

        Resolves dependencies and initializes plugins so that
        each plugin's dependencies are initialized first.
        """
        order = self._resolve_dependencies()

        for name in order:
            plugin = self._plugins[name]
            if plugin.is_initialized:
                continue

            # Check dependencies are initialized
            for dep in plugin.dependencies:
                dep_plugin = self._plugins.get(dep)
                if not dep_plugin or not dep_plugin.is_initialized:
                    raise RuntimeError(
                        f"Plugin '{name}' depends on '{dep}' which is not initialized"
                    )

            try:
                plugin._runtime = runtime
                plugin.initialize(runtime)
                plugin._initialized = True
                self._init_order.append(name)
                logger.info(f"Initialized plugin: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin '{name}': {e}")
                raise

    def shutdown_all(self) -> None:
        """Shutdown all plugins in reverse initialization order."""
        for name in reversed(self._init_order):
            plugin = self._plugins.get(name)
            if plugin and plugin.is_initialized:
                try:
                    plugin.shutdown()
                    plugin._initialized = False
                    logger.info(f"Shut down plugin: {name}")
                except Exception as e:
                    logger.error(f"Error shutting down plugin '{name}': {e}")

        self._init_order.clear()

    def _resolve_dependencies(self) -> List[str]:
        """Topological sort of plugins by dependencies."""
        visited = set()
        order = []

        def visit(name: str, path: List[str]):
            if name in path:
                cycle = " -> ".join(path + [name])
                raise RuntimeError(f"Circular plugin dependency: {cycle}")
            if name in visited:
                return
            if name not in self._plugins:
                raise RuntimeError(f"Missing plugin dependency: {name}")

            path.append(name)
            for dep in self._plugins[name].dependencies:
                visit(dep, path)
            path.pop()

            visited.add(name)
            order.append(name)

        for name in self._plugins:
            visit(name, [])

        return order

    def __len__(self) -> int:
        return len(self._plugins)

    def __contains__(self, name: str) -> bool:
        return name in self._plugins

    def __repr__(self) -> str:
        active = sum(1 for p in self._plugins.values() if p.is_initialized)
        return f"PluginRegistry({len(self._plugins)} plugins, {active} active)"
