"""
agent/loop.py

Factor 8 - Own your control flow.
Factor 9 - Compact errors into the context window.
Factor 12 - Make your agent a stateless reducer.
============================================================
The agent loop is the heart of the reasoning engine.

Key design decisions
--------------------
• `step()` is a *pure stateless reducer*: it takes an (AgentState, client,
  config) and returns the next AgentState. No global variables, no hidden
  mutation. This makes it trivially testable and resumable (Factor 12).

• `run()` is the iterative driver that calls `step()` until the agent
  reaches a terminal state (DONE or ERROR). Callers can pass a `callback`
  to observe each intermediate state (useful for streaming UIs).

• Tool calls are dispatched via `tool_handlers.dispatch_all()` — the loop
  itself contains *no* domain logic, only control flow.

• On tool failures the error string is compacted into
  `state.last_error` which `AgentState.api_messages()` will inject into
  the context window on the next step (Factor 9).

• The loop is capped at `max_steps` to prevent infinite loops.
"""
import logging

from __future__ import annotations

from typing import Any, Callable

from openai import OpenAI

from .state import AgentState, AgentStatus
from .tools import TOOLS
from .tool_handlers import dispatch_all, serialise_tool_calls
from .prompts import SYSTEM_PROMPT, build_error_context

# ── Configuration 

DEFAULT_MODEL = "gpt-5.1"
DEFAULT_MAX_STEPS = 20       # safety cap to prevent runaway loops


# Stateless reducer 

def step(
    state: AgentState,
    client: OpenAI,
    model: str = DEFAULT_MODEL,
    system_prompt: str = SYSTEM_PROMPT,
) -> AgentState:
    """
    Factor 12 - Stateless reducer.

    Takes the *current* AgentState and returns the *next* AgentState.
    This function has no side-effects beyond the OpenAI API call.

    Possible state transitions
    --------------------------
    RUNNING → AWAITING_TOOL  (model requested tool calls)
    AWAITING_TOOL → RUNNING  (tool results appended, loop continues)
    RUNNING → DONE           (model produced a final answer)
    any → ERROR              (unrecoverable API error)
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=state.api_messages(system_prompt),
            tools=TOOLS,
        )
    except Exception as exc:
        # Factor 9: compact the API error into state
        return state.with_status(
            AgentStatus.ERROR,
            error=f"OpenAI API error: {type(exc).__name__}: {exc}",
        )

    choice = completion.choices[0]
    message = choice.message
    finish_reason = choice.finish_reason

    # Branch: model wants to call tools
    if finish_reason == "tool_calls" and message.tool_calls:
        tool_calls_serialised = serialise_tool_calls(message.tool_calls)

        # Append the assistant message (with tool_calls) to history
        new_state = state.add_assistant_message(
            content=message.content or "",
            tool_calls=tool_calls_serialised,
        ).with_status(AgentStatus.AWAITING_TOOL)

        # Dispatch all tools (Factor 1: NL → tool calls)
        results, errors = dispatch_all(message.tool_calls)

        # Append each tool result message
        for result in results:
            new_state = new_state.add_tool_result(
                tool_call_id=result.tool_call_id,
                content=result.content,
            )

        # Factor 9: compact errors into the context window for the next step
        error_ctx = build_error_context(errors) if errors else None
        return new_state.with_status(AgentStatus.RUNNING, error=error_ctx)

    # Branch: model produced a final answer
    final_content = message.content or ""
    return state.add_assistant_message(content=final_content).model_copy(
        update={
            "status": AgentStatus.DONE,
            "last_response": final_content,
            "last_error": None,
        }
    )


# Iterative driver

def run(
    state: AgentState,
    client: OpenAI,
    model: str = DEFAULT_MODEL,
    system_prompt: str = SYSTEM_PROMPT,
    max_steps: int = DEFAULT_MAX_STEPS,
    on_step: Callable[[AgentState], None] | None = None,
) -> AgentState:
    """
    Factor 8 - Own your control flow.

    Drive the agent loop until it reaches DONE, ERROR, or `max_steps`.

    Parameters
    ----------
    state        : Starting AgentState (must contain the latest user message).
    client       : Authenticated OpenAI client.
    model        : Chat model to use.
    system_prompt: Override the default system prompt (Factor 3).
    max_steps    : Hard cap on loop iterations to prevent runaway agents.
    on_step      : Optional callback called after each step with the new
                   state — useful for streaming intermediate tool statuses
                   to a UI layer (Factor 7/11).

    Returns
    -------
    The final AgentState after the loop terminates.
    """
    current = state.with_status(AgentStatus.RUNNING)

    for _ in range(max_steps):
        current = step(current, client, model=model, system_prompt=system_prompt)

        if on_step is not None:
            on_step(current)

        if current.status in (AgentStatus.DONE, AgentStatus.ERROR):
            break
    else:
        # Exceeded max_steps — treat as an error so the UI can inform the user
        current = current.with_status(
            AgentStatus.ERROR,
            error=f"Agent exceeded the maximum number of steps ({max_steps}).",
        )

    return current


# Tool-call names for UI consumption

def pending_tool_names(state: AgentState) -> list[str]:
    """Return human-readable tool names from the last model response."""
    if state.status != AgentStatus.AWAITING_TOOL:
        return []
    # Pull from the last assistant message that carried tool_calls
    for msg in reversed(state.messages):
        if msg.role == "assistant" and msg.tool_calls:
            return [tc["function"]["name"] for tc in msg.tool_calls]
        elif state.status == AgentStatus.AWAITING_TOOL:
            # Unexpected: status says we're awaiting tools, but no tool_calls found
            logging.warning(f"Pending tool names requested but no tool_calls found in state: {state}")

    return []
