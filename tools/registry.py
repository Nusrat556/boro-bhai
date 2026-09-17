"""Simple registry for BORO BHAI tools."""

from __future__ import annotations

from tools.calculator import calculate


class ToolRegistry:
    """Discover and resolve tools without a framework."""

    def __init__(self):
        self._tools = {
            "calculator": calculate,
        }

    def register(self, name: str, func):
        """Register a new callable tool by name."""
        self._tools[name] = func

    def get(self, name: str):
        """Return a tool function by name or raise KeyError."""
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Tool '{name}' is not registered.") from exc

    def list_tools(self):
        """Return the tool names currently available."""
        return list(self._tools.keys())


def build_registry() -> ToolRegistry:
    """Return the default registry used by the agent."""
    return ToolRegistry()
