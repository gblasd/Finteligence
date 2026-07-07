"""
app/prompts/registry.py

Layer 3 – Prompt registry.
Maps task names to versioned prompt strings. Any code that needs a prompt
should call `PromptRegistry.get(task)` rather than hardcoding a string.
"""
from __future__ import annotations

from app.prompts.templates import (
    FINANCIAL_ANALYST_SYSTEM,
    SECURITY_GUARDRAIL,
    DIDACTIC_GOAL,
    STYLE_GUIDE,
    QUERY_REWRITE_PROMPT,
    QUERY_DECOMPOSE_PROMPT,
    INPUT_GUARD_PROMPT,
    OUTPUT_FILTER_PROMPT,
)


_REGISTRY: dict[str, dict[str, str]] = {
    "financial_system": {
        "v1": "\n\n".join([FINANCIAL_ANALYST_SYSTEM, SECURITY_GUARDRAIL, DIDACTIC_GOAL, STYLE_GUIDE])
    },
    "query_rewrite": {
        "v1": QUERY_REWRITE_PROMPT,
    },
    "query_decompose": {
        "v1": QUERY_DECOMPOSE_PROMPT,
    },
    "input_guard": {
        "v1": INPUT_GUARD_PROMPT,
    },
    "output_filter": {
        "v1": OUTPUT_FILTER_PROMPT,
    },
}


class PromptRegistry:
    """Central prompt manager — maps task → versioned prompt string."""

    @staticmethod
    def get(task: str, version: str = "v1") -> str:
        """
        Retrieve the prompt for *task* at *version*.

        Raises
        ------
        KeyError if the task or version is not registered.
        """
        try:
            return _REGISTRY[task][version]
        except KeyError:
            available = list(_REGISTRY.keys())
            raise KeyError(
                f"Prompt '{task}' (version '{version}') not found. "
                f"Available tasks: {available}"
            )

    @staticmethod
    def list_tasks() -> list[str]:
        """Return all registered task names."""
        return list(_REGISTRY.keys())

    @staticmethod
    def register(task: str, version: str, prompt: str) -> None:
        """Register a new prompt at runtime (e.g. from a config file)."""
        if task not in _REGISTRY:
            _REGISTRY[task] = {}
        _REGISTRY[task][version] = prompt
