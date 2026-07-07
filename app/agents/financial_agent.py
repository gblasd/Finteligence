"""
app/agents/financial_agent.py

Layer 2 - Financial analysis agent.
The core reasoning worker. Drives the tool-calling loop using the
Factor-Agents state machine from agent/ and exposes a clean `.run()` API.
"""
from __future__ import annotations

from openai import OpenAI

from agent.state import AgentState, AgentStatus
from agent.loop import run as run_loop
from agent.prompts import SYSTEM_PROMPT
from app.agents.tools import TOOLS
from observability.tracer import Tracer


class FinancialAgent:
    """
    Thin façade over the Factor-Agents loop for financial analysis tasks.

    Responsibilities (single)
    -------------------------
    Run the multi-step tool-calling reasoning loop for a financial query
    and return the final text response.
    """

    def __init__(self, client: OpenAI, model: str = "gpt-5.1") -> None:
        self._client = client
        self._model  = model
        self._tracer = Tracer()

    def run(
        self,
        query: str,
        history: list[dict] | None = None,
        on_step=None,
    ) -> str:
        """
        Run the agent loop for *query* and return the final answer text.

        Parameters
        ----------
        query   : The (possibly rewritten) user question.
        history : Previous conversation turns (OpenAI message dicts).
        on_step : Optional callback called after each step (for UI streaming).
        """
        span = self._tracer.start_span("financial_agent.run", query=query)

        # Seed state with conversation history
        state = AgentState()
        if history:
            from agent.state import Message
            for msg in history:
                state = state.model_copy(
                    update={"messages": state.messages + [Message(**msg)]}
                )

        state = state.add_user_message(query)
        final = run_loop(
            state=state,
            client=self._client,
            model=self._model,
            system_prompt=SYSTEM_PROMPT,
            on_step=on_step,
        )

        if final.status == AgentStatus.ERROR:
            span.log("agent_error", error=final.last_error)
            span.finish(error=True)
            return f"Lo siento, ocurrió un error: {final.last_error}"

        span.finish()
        return final.last_response
