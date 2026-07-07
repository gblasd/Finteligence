"""
prompts.py — Backwards-compatibility shim.

The canonical prompts now live in `agent/prompts.py`.
This module re-exports `SYSTEM_PROMPT` as `stronger_prompt` so that
any external code still importing from this path continues to work.
"""
from agent.prompts import SYSTEM_PROMPT as stronger_prompt  # noqa: F401

__all__ = ["stronger_prompt"]