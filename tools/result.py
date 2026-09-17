"""Common tool result shape for BORO BHAI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """A simple internal result format used by tool calls."""

    success: bool
    tool_name: str
    result: Any = None
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }
