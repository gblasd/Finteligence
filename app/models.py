"""
app/models.py

Shared Pydantic data models used across all layers.
Centralising models here prevents circular imports and keeps the data
contract clear and versioned.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Conversation ──────────────────────────────────────────────────────────────

class ConversationMessage(BaseModel):
    """A single turn in a conversation session."""
    role: str
    content: str
    extra: dict[str, Any] = Field(default_factory=dict)


# ── Pipeline I/O ──────────────────────────────────────────────────────────────

class PipelineInput(BaseModel):
    """Input to the main AI pipeline."""
    user_message: str
    session_id: str = "default"


class PipelineOutput(BaseModel):
    """Output from the main AI pipeline."""
    response: str
    blocked: bool = False
    from_cache: bool = False
    trace_id: str = ""
    error: Optional[str] = None
