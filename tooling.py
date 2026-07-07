"""
tooling.py — Backwards-compatibility shim.

The canonical tool registry and dispatch now live in:
  • agent/tools.py          — schemas
  • agent/tool_handlers.py  — dispatch

This module re-exports the symbols that existing code may import
from this path, so nothing breaks during migration.
"""
from agent.tools import TOOLS as tools  # noqa: F401
from agent.tool_handlers import dispatch_all  # noqa: F401


def handle_tool_calls(tool_calls):
    """
    Legacy wrapper around the new dispatch layer.

    Returns the flat list of tool-result message dicts that the old
    App.py expected. New code should use `agent.tool_handlers.dispatch_all`
    directly.
    """
    results, _ = dispatch_all(tool_calls)
    return [r.to_message() for r in results]


__all__ = ["tools", "handle_tool_calls"]