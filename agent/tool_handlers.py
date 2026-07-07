"""
agent/tool_handlers.py

Factor 1 - Natural language to tool calls (dispatch layer).
Factor 9 - Compact errors into the context window.
============================================================
This module owns the *execution* side of tool calls:
  • A typed dispatch table maps tool names → Python callables.
  • `dispatch_tool_call` runs one tool call and returns a structured result.
  • `dispatch_all` runs all tool calls for one agent turn and returns
    tool-result messages ready to be appended to the conversation.

Error handling:
  Every tool invocation is wrapped in a try/except. On failure the error
  is compacted into a short, descriptive string that will be injected into
  the context window (Factor 9) so the model can adapt its next action.
"""

from __future__ import annotations

import json
import traceback
from typing import Any, Callable

from utils import (
    get_income_statement,
    get_balance_sheet,
    get_cashflow_statement,
    get_earnings,
    get_call_transcripts,
    get_intrinsic_value,
)

# Dispatch table
# Each entry maps a tool name (matches the schema in tools.py) to its Python
# callable.  Adding a new tool = add one entry here + one schema in tools.py.

_DISPATCH: dict[str, Callable[..., Any]] = {
    "get_income_statement":   get_income_statement,
    "get_balance_sheet":      get_balance_sheet,
    "get_cashflow_statement": get_cashflow_statement,
    "get_earnings":           get_earnings,
    "get_call_transcripts":   get_call_transcripts,
    "get_intrinsic_value":    get_intrinsic_value,
}


# Single tool dispatch

class ToolResult:
    """Lightweight container for a single tool execution result."""

    def __init__(self, tool_call_id: str, name: str, content: str, error: str | None = None):
        self.tool_call_id = tool_call_id
        self.name = name
        self.content = content          # JSON-serialised result or error payload
        self.error = error              # Non-None when execution failed

    def to_message(self) -> dict[str, Any]:
        """Return the OpenAI tool-result message dict."""
        return {
            "role": "tool",
            "content": self.content,
            "tool_call_id": self.tool_call_id,
        }


def dispatch_tool_call(tool_call_id: str, name: str, arguments: dict[str, Any]) -> ToolResult:
    """
    Execute a single tool call and return a ToolResult.

    Factor 9 - on any exception the error is captured and serialised
    as a compact JSON payload so the model sees exactly what went wrong.
    """
    handler = _DISPATCH.get(name)
    if handler is None:
        error_msg = f"Unknown tool '{name}'. Available: {list(_DISPATCH.keys())}"
        return ToolResult(
            tool_call_id=tool_call_id,
            name=name,
            content=json.dumps({"error": error_msg}),
            error=error_msg,
        )

    try:
        result = handler(**arguments)
        return ToolResult(
            tool_call_id=tool_call_id,
            name=name,
            content=json.dumps(result),
        )
    except Exception as exc:
        # Compact the error: type, message, and a short traceback snippet
        tb_lines = traceback.format_exc().splitlines()
        compact_tb = " | ".join(tb_lines[-3:])  # last 3 lines only
        error_msg = f"{type(exc).__name__}: {exc} — {compact_tb}"
        return ToolResult(
            tool_call_id=tool_call_id,
            name=name,
            content=json.dumps({"error": error_msg}),
            error=error_msg,
        )


# Batch dispatch

def dispatch_all(tool_calls: list[Any]) -> tuple[list[ToolResult], list[str]]:
    """
    Dispatch every tool call in a model response and return:
      (list[ToolResult], list[error_strings])

    The caller appends results to the conversation and may inject
    any errors into state.last_error (Factor 9).
    """
    results: list[ToolResult] = []
    errors: list[str] = []

    for tc in tool_calls:
        tool_call_id = tc.id
        name = tc.function.name
        try:
            arguments = json.loads(tc.function.arguments)
        except json.JSONDecodeError as e:
            error_msg = f"Could not parse arguments for '{name}': {e}"
            errors.append(error_msg)
            results.append(
                ToolResult(
                    tool_call_id=tool_call_id,
                    name=name,
                    content=json.dumps({"error": error_msg}),
                    error=error_msg,
                )
            )
            continue

        result = dispatch_tool_call(tool_call_id, name, arguments)
        results.append(result)
        if result.error:
            errors.append(result.error)

    return results, errors


# Serialise tool_calls from a model response

def serialise_tool_calls(tool_calls: list[Any]) -> list[dict[str, Any]]:
    """Convert OpenAI SDK tool_call objects into plain dicts for the message list."""
    return [
        {
            "id": tc.id,
            "type": tc.type,
            "function": {
                "name": tc.function.name,
                "arguments": tc.function.arguments,
            },
        }
        for tc in tool_calls
    ]
