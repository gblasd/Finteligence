"""
tests/test_routing.py

Layer 9 – Query routing tests.
Verifies that QueryRouter sends queries to the correct destination.
"""
import pytest
from app.services.query_router import QueryRouter, RouteDestination


@pytest.fixture
def router() -> QueryRouter:
    return QueryRouter()


class TestQueryRouter:
    def test_financial_query_routes_to_agent(self, router):
        dest = router.route("What is Apple's income statement?")
        assert dest == RouteDestination.FINANCIAL_AGENT

    def test_valuation_query_routes_to_intrinsic_value(self, router):
        dest = router.route("What is the intrinsic value of NVDA?")
        assert dest == RouteDestination.INTRINSIC_VALUE

    def test_earnings_call_routes_correctly(self, router):
        dest = router.route("What did Tesla say in their earnings call?")
        assert dest == RouteDestination.EARNINGS_CALL

    def test_out_of_scope_gets_blocked(self, router):
        dest = router.route("Book me a flight to Paris")
        assert dest == RouteDestination.SECURITY_BLOCK

    def test_crypto_query_gets_blocked(self, router):
        dest = router.route("What is the bitcoin price today?")
        assert dest == RouteDestination.SECURITY_BLOCK
