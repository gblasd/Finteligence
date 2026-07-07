"""
app/agents/tools/financial_tools.py

Layer 2 - Financial data tools.
Thin wrappers over utils.py that add logging and structured error handling.
Each function matches the schema defined in agent/tools.py.
"""
from __future__ import annotations

from agent.utils import (
    get_income_statement,
    get_balance_sheet,
    get_cashflow_statement,
    get_earnings,
    get_call_transcripts,
    get_intrinsic_value,
)
from observability.tracer import Tracer

_tracer = Tracer()


def fetch_income_statement(ticker: str, period: str = "anual") -> dict:
    span = _tracer.start_span("tool.income_statement", ticker=ticker, period=period)
    try:
        result = get_income_statement(ticker, period)
        span.finish()
        return result
    except Exception as e:
        span.finish(error=True)
        raise


def fetch_balance_sheet(ticker: str, period: str = "anual") -> dict:
    span = _tracer.start_span("tool.balance_sheet", ticker=ticker, period=period)
    try:
        result = get_balance_sheet(ticker, period)
        span.finish()
        return result
    except Exception as e:
        span.finish(error=True)
        raise


def fetch_cashflow_statement(ticker: str, period: str = "anual") -> dict:
    span = _tracer.start_span("tool.cashflow", ticker=ticker, period=period)
    try:
        result = get_cashflow_statement(ticker, period)
        span.finish()
        return result
    except Exception as e:
        span.finish(error=True)
        raise


def fetch_earnings(ticker: str, period: str = "anual") -> dict:
    span = _tracer.start_span("tool.earnings", ticker=ticker, period=period)
    try:
        result = get_earnings(ticker, period)
        span.finish()
        return result
    except Exception as e:
        span.finish(error=True)
        raise


def fetch_intrinsic_value(ticker: str) -> dict:
    span = _tracer.start_span("tool.intrinsic_value", ticker=ticker)
    try:
        result = get_intrinsic_value(ticker)
        span.finish()
        return result
    except Exception as e:
        span.finish(error=True)
        raise


def fetch_call_transcripts(ticker: str, quarter: str) -> dict:
    span = _tracer.start_span("tool.call_transcripts", ticker=ticker, quarter=quarter)
    try:
        result = get_call_transcripts(ticker, quarter)
        span.finish()
        return result
    except Exception as e:
        span.finish(error=True)
        raise
