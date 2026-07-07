"""
agent/state.py

Factor 5 - Unify execution state & business state.
=========================================================
A single Pydantic model is the *only* source of truth for both
what the agent is doing right now (execution state) and what the
user conversation contains (business state).

Keeping them unified means:
  • No hidden "shadow" state scattered across modules.
  • The full state can be serialised, stored, and resumed trivially
    (Factor 6 - Launch/Pause/Resume with simple APIs).
  • The agent loop can be implemented as a pure stateless reducer
    (Factor 12) that receives this object and returns the next one.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# Execution phases

class AgentStatus(str, Enum):
    """Tracks where in the reasoning loop the agent currently is."""
    IDLE = "idle"
    RUNNING = "running"
    AWAITING_TOOL = "awaiting_tool"
    DONE = "done"
    ERROR = "error"


# Message types

class Message(BaseModel):
    """A single turn in the conversation history."""
    role: str          # "user" | "assistant" | "tool" | "system"
    content: str = ""
    tool_calls: Optional[list[dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    audio: Optional[bytes] = None  # TTS bytes stored alongside the message

    def to_api_dict(self) -> dict[str, Any]:
        """Serialise to the format expected by the OpenAI Chat Completions API."""
        d: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls is not None:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        return d


# Unified agent state

class AgentState(BaseModel):
    """
    Single source of truth that unifies execution + business state.

    Execution state fields
    ----------------------
    status          : current phase of the agent loop
    last_error      : compact error message injected into context (Factor 9)
    pending_tool_calls : tool calls waiting to be dispatched

    Business state fields
    ---------------------
    messages        : full conversation history shown to and from the model
    last_response   : final streamed text from the last assistant turn
    audio_bytes     : TTS audio generated for the last assistant turn
    """

    # Execution state
    status: AgentStatus = AgentStatus.IDLE
    last_error: Optional[str] = None
    pending_tool_calls: list[dict[str, Any]] = Field(default_factory=list)

    # Business state
    messages: list[Message] = Field(default_factory=list)
    last_response: str = ""
    audio_bytes: Optional[bytes] = None

    # Helpers

    def add_user_message(self, content: str) -> "AgentState":
        """Return a new state with the user message appended (immutable update)."""
        return self.model_copy(
            update={"messages": self.messages + [Message(role="user", content=content)]}
        )

    def add_assistant_message(self, content: str, tool_calls: Optional[list] = None) -> "AgentState":
        return self.model_copy(
            update={
                "messages": self.messages + [
                    Message(role="assistant", content=content, tool_calls=tool_calls)
                ]
            }
        )

    def add_tool_result(self, tool_call_id: str, content: str) -> "AgentState":
        return self.model_copy(
            update={
                "messages": self.messages + [
                    Message(role="tool", content=content, tool_call_id=tool_call_id)
                ]
            }
        )

    def with_status(self, status: AgentStatus, error: Optional[str] = None) -> "AgentState":
        return self.model_copy(update={"status": status, "last_error": error})

    def api_messages(self, system_prompt: str) -> list[dict[str, Any]]:
        """
        Build the exact message list sent to the API.

        Factor 3 - Own your context window:
          • Prepends the system prompt as an assistant turn (OpenAI convention).
          • Compacts any stored error into a synthetic user message so the model
            can adapt (Factor 9).
          • Excludes binary audio bytes which would bloat the context.
        """
        context: list[dict[str, Any]] = [
            {"role": "assistant", "content": system_prompt}
        ]
        for msg in self.messages:
            context.append(msg.to_api_dict())

        # Factor 9 – Compact error into the context window
        if self.last_error:
            context.append({
                "role": "user",
                "content": (
                    f"[SYSTEM NOTE] The previous operation failed with the following error. "
                    f"Please adjust your next action accordingly:\n\n{self.last_error}"
                ),
            })
        return context

    # Serialisation (Factor 6 – Launch / Pause / Resume)

    def to_json(self) -> str:
        """
        Serialise the full state to JSON.

        Audio bytes are excluded from both the top-level `audio_bytes` field
        *and* from every `Message.audio` field in the messages list.
        Raw MP3/WAV bytes contain non-UTF-8 sequences that Pydantic cannot
        serialise to JSON — and audio only serves as replay data in the UI,
        so it doesn't need to survive a round-trip through session state.
        """
        clean_messages = [
            msg.model_copy(update={"audio": None}) for msg in self.messages
        ]
        return self.model_copy(
            update={"audio_bytes": None, "messages": clean_messages}
        ).model_dump_json()

    @classmethod
    def from_json(cls, raw: str) -> "AgentState":
        """Restore a previously serialised state."""
        return cls.model_validate_json(raw)
