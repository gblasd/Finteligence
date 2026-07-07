"""
app/services/conversation.py

Layer 1 – Conversation memory manager.
Manages session history, user context, and continuity across turns so
the agent understands when the second question depends on the first.
"""
from __future__ import annotations
from typing import Any
from app.models import ConversationMessage


class ConversationManager:
    """
    Manages per-session conversation history.

    Responsibilities
    ----------------
    - Store and retrieve the ordered message history for a session.
    - Provide a clean interface for appending new turns.
    - Support clearing / resetting the session.
    - (Future) Summarise older turns to keep the context window tight.
    """

    def __init__(self) -> None:
        self._history: list[ConversationMessage] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def append(self, role: str, content: str, extra: dict[str, Any] | None = None) -> None:
        """Append a new message to the conversation."""
        self._history.append(
            ConversationMessage(role=role, content=content, extra=extra or {})
        )

    def get_history(self) -> list[ConversationMessage]:
        """Return the full, ordered conversation history."""
        return list(self._history)

    def get_api_messages(self) -> list[dict[str, Any]]:
        """Return history serialised as OpenAI-compatible message dicts."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self._history
        ]

    def clear(self) -> None:
        """Reset the session (e.g. when the user clicks 'Clear conversation')."""
        self._history.clear()

    def __len__(self) -> int:
        return len(self._history)
