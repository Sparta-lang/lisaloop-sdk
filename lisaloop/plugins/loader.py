"""
Plugin loader — discovers and loads plugins from files and directories.

Usage:
    from lisaloop.plugins import PluginLoader

    loader = PluginLoader()

    # Load from a single file
    plugins = loader.load_file("plugins/my_plugin.py")

    # Load from a directory
    plugins = loader.load_directory("plugins/")

    # Load from a package
    plugins = loader.load_package("lisaloop_poker_extras")
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import List

from lisaloop.plugins.base import Plugin

logger = logging.getLogger("lisaloop.plugins.loader")


class PluginLoader:
    """
    Discovers and instantiates plugins from Python files, directories,
    or installed packages.
    """

    def load_file(self, path: str) -> List[Plugin]:
        """Load all Plugin subclasses from a Python file."""
        p = Path(path)
        if not p.exists():
            logger.error(f"Plugin file not found: {path}")
            return []

        try:
            spec = importlib.util.spec_from_file_location(f"plugin_{p.stem}", p)
            module = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(module)  # type: ignore
            return self._extract_plugins(module)
        except Exception as e:
            logger.error(f"Failed to load plugin from {path}: {e}")
            return []

    def load_directory(self, directory: str) -> List[Plugin]:
        """Load all plugins from .py files in a directory."""
        d = Path(directory)
        if not d.is_dir():
            logger.error(f"Plugin directory not found: {directory}")
            return []

        plugins = []
        for f in sorted(d.glob("*.py")):
            if f.name.startswith("_"):
                continue
            plugins.extend(self.load_file(str(f)))

        logger.info(f"Loaded {len(plugins)} plugins from {directory}")
        return plugins

    def load_package(self, package_name: str) -> List[Plugin]:
        """Load plugins from an installed Python package."""
        try:
            module = importlib.import_module(package_name)
            return self._extract_plugins(module)
        except ImportError:
            logger.error(f"Package not found: {package_name}")
            return []

    def _extract_plugins(self, module) -> List[Plugin]:
        """Find and instantiate all Plugin subclasses in a module."""
        plugins = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Plugin)
                and attr is not Plugin
                and not attr.__name__.startswith("_")
            ):
                try:
                    instance = attr()
                    plugins.append(instance)
                    logger.info(f"Discovered plugin: {instance.name} from {module.__name__}")
                except Exception as e:
                    logger.error(f"Failed to instantiate {attr.__name__}: {e}")

        return plugins
