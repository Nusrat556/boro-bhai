"""Simple registry for BORO BHAI tools."""

from __future__ import annotations

from tools.calculator import calculate
from tools.csv_analyzer import analyze_csv
from tools.file_reader import read_text_file
from tools.pdf_reader import read_pdf_text
from tools.web_search import web_search


class ToolRegistry:
    """Discover and resolve tools without a framework."""

    def __init__(self):
        self._tools = {
            "calculator": calculate,
            "text_file": read_text_file,
            "csv": analyze_csv,
            "pdf": read_pdf_text,
            "web_search": web_search,
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
