"""
app/services/query_router.py

Layer 1 - Query router.
Decides where a user request should go based on intent classification.
This keeps the main agent loop from having to handle every edge case.
"""
from __future__ import annotations

from enum import Enum


class RouteDestination(str, Enum):
    FINANCIAL_AGENT   = "financial_agent"   # Standard analysis request
    INTRINSIC_VALUE   = "intrinsic_value"   # Valuation request
    EARNINGS_CALL     = "earnings_call"     # Earnings transcript request
    SECURITY_BLOCK    = "security_block"    # Out-of-domain or unsafe
    GENERAL           = "general"           # Catch-all


# Simple keyword-based routing table (extend with LLM classifier for prod)
_INTRINSIC_KEYWORDS  = {"intrinsic", "valuation", "fair value", "undervalued", "overvalued", "dcf"}
_EARNINGS_KEYWORDS   = {"earnings call", "transcript", "conference call", "investor call"}
_BLOCK_KEYWORDS      = {"flight", "hotel", "pizza", "weather", "crypto", "bitcoin", "forex"}


class QueryRouter:
    """Routes incoming queries to the appropriate pipeline."""

    def route(self, query: str) -> RouteDestination:
        """
        Classify *query* and return the appropriate destination.

        Priority: SECURITY_BLOCK > INTRINSIC_VALUE > EARNINGS_CALL > FINANCIAL_AGENT
        """
        lower = query.lower()

        if any(kw in lower for kw in _BLOCK_KEYWORDS):
            return RouteDestination.SECURITY_BLOCK

        if any(kw in lower for kw in _INTRINSIC_KEYWORDS):
            return RouteDestination.INTRINSIC_VALUE

        if any(kw in lower for kw in _EARNINGS_KEYWORDS):
            return RouteDestination.EARNINGS_CALL

        return RouteDestination.FINANCIAL_AGENT
