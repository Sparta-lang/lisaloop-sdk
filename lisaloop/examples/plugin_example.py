"""
Example Plugin — shows how to extend the framework.

This plugin adds a custom logging agent and registers
it with the runtime.
"""

from lisaloop.plugins import Plugin, PluginType
from lisaloop.agents.base import Agent
from lisaloop.core.state import Action, GameState


class LoggingAgent(Agent):
    """An agent that logs every decision to stdout."""
    name = "LoggerBot"
    version = "1.0"
    description = "Logs every decision for debugging."

    def decide(self, state: GameState) -> Action:
        print(f"  [LoggerBot] Hand #{state.hand_number} | "
              f"{state.street.name} | Pot: ${state.pot.total:.2f}")
        if state.can_check():
            return Action.check()
        return Action.fold()


class LoggingPlugin(Plugin):
    """Plugin that adds the LoggingAgent to the framework."""
    name = "logging-plugin"
    version = "1.0"
    type = PluginType.AGENT
    description = "Adds a debug logging agent"

    def initialize(self, runtime):
        runtime.register_agent(LoggingAgent())
        print(f"  [LoggingPlugin] Registered LoggingAgent")

    def shutdown(self):
        print(f"  [LoggingPlugin] Shutting down")
