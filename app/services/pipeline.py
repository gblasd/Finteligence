"""
app/services/pipeline.py

Layer 1 - Main AI pipeline orchestrator.
Coordinates query rewriting → routing → agent execution → caching.
This is the single entry point for processing a user turn.
"""
from __future__ import annotations

from openai import OpenAI

from app.models import PipelineInput, PipelineOutput
from app.services.query_rewriter import QueryRewriter
from app.services.query_router import QueryRouter, RouteDestination
from app.services.semantic_cache import SemanticCache
from app.services.conversation import ConversationManager
from app.agents.financial_agent import FinancialAgent
from app.security.input_guard import InputGuard
from app.security.output_filter import OutputFilter
from observability.tracer import Tracer
from observability.cost_tracker import CostTracker


class AIPipeline:
    """
    Orchestrates the full request-response flow:

    User input
      → InputGuard   (Layer 4)
      → QueryRewriter (Layer 1)
      → QueryRouter   (Layer 1)
      → SemanticCache (Layer 1)
      → FinancialAgent (Layer 2)
      → OutputFilter  (Layer 4)
      → Response
    """

    def __init__(self, client: OpenAI) -> None:
        self._client      = client
        self._rewriter    = QueryRewriter(client)
        self._router      = QueryRouter()
        self._cache       = SemanticCache(client)
        self._input_guard = InputGuard()
        self._out_filter  = OutputFilter()
        self._agent       = FinancialAgent(client)
        self._tracer      = Tracer()
        self._cost        = CostTracker()

    def run(self, inp: PipelineInput, conversation: ConversationManager) -> PipelineOutput:
        """Process one user turn end-to-end."""
        span = self._tracer.start_span("pipeline.run", query=inp.user_message)

        # 1. Security: guard the raw input
        guard_result = self._input_guard.check(inp.user_message)
        if not guard_result.is_safe:
            span.finish(blocked=True)
            return PipelineOutput(
                response=guard_result.rejection_message,
                blocked=True,
                trace_id=span.trace_id,
            )

        # 2. Rewrite query for clarity
        rewritten = self._rewriter.rewrite(inp.user_message)
        span.log("query_rewritten", rewritten=rewritten)

        # 3. Route the query
        destination = self._router.route(rewritten)
        span.log("routed", destination=destination.value)

        if destination == RouteDestination.SECURITY_BLOCK:
            response = (
                "💡 Puedo ayudarte exclusivamente con **análisis fundamental y educación "
                "financiera**. Esa solicitud está fuera de mi alcance."
            )
            span.finish(blocked=True)
            return PipelineOutput(response=response, blocked=True, trace_id=span.trace_id)

        # 4. Check semantic cache
        cached = self._cache.get(rewritten)
        if cached:
            span.log("cache_hit")
            span.finish(cached=True)
            return PipelineOutput(response=cached, from_cache=True, trace_id=span.trace_id)

        # 5. Run the financial agent
        conversation.append("user", inp.user_message)
        agent_response = self._agent.run(
            query=rewritten,
            history=conversation.get_api_messages(),
        )
        conversation.append("assistant", agent_response)

        # 6. Filter output
        filtered = self._out_filter.filter(agent_response)
        span.log("output_filtered")

        # 7. Store in semantic cache
        self._cache.set(rewritten, filtered)

        span.finish() 
        return PipelineOutput(response=filtered, trace_id=span.trace_id)
