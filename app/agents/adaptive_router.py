"""
app/agents/adaptive_router.py

Layer 2 - Adaptive router agent.
Acts as a smart traffic controller: dynamically decides which agent or
tool should handle the current request based on context.
"""
from __future__ import annotations

from app.services.query_router import QueryRouter, RouteDestination


class AdaptiveRouter:
    """
    An agent-level router that can adapt based on runtime context
    (e.g., conversation depth, tool availability, query complexity).

    Delegates simple routing to `QueryRouter` (keyword-based) and
    can be extended with LLM-based classification for edge cases.
    """

    def __init__(self) -> None:
        self._base_router = QueryRouter()

    def route(self, query: str, context: dict | None = None) -> RouteDestination:
        """
        Route *query* considering optional runtime *context*.

        context keys (optional)
        -----------------------
        conversation_length : int  — number of prior turns
        last_tool_used      : str  — name of the last tool called
        """
        destination = self._base_router.route(query)

        # Future: override with LLM-based classification when context signals
        # a complex multi-step request (e.g. conversation_length > 5).

        return destination
