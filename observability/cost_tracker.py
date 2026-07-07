"""
observability/cost_tracker.py

Layer 6 - Cost tracker.
Tracks token usage and estimated USD cost per request so surprise bills
are caught early and expensive features can be optimised.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


# Approximate pricing per 1k tokens (update when OpenAI changes pricing)
_PRICE_PER_1K: dict[str, dict[str, float]] = {
    "gpt-5.1":          {"input": 0.002,  "output": 0.008},
    "gpt-4o-mini":      {"input": 0.00015, "output": 0.0006},
    "gpt-4o":           {"input": 0.0025, "output": 0.010},
    "whisper-1":        {"per_minute": 0.006},
    "gpt-4o-mini-tts":  {"per_char": 0.000015},
}


@dataclass
class UsageRecord:
    timestamp:     str
    model:         str
    feature:       str          # e.g. "chat", "tts", "stt", "embedding"
    input_tokens:  int = 0
    output_tokens: int = 0
    cost_usd:      float = 0.0


class CostTracker:
    """Tracks and estimates AI API costs per request and per feature."""

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []

    def record_chat(self, model: str, input_tokens: int, output_tokens: int, feature: str = "chat") -> float:
        """Record a chat completion call and return the estimated cost."""
        pricing = _PRICE_PER_1K.get(model, {"input": 0.002, "output": 0.008})
        cost = (
            input_tokens  / 1000 * pricing.get("input", 0)
            + output_tokens / 1000 * pricing.get("output", 0)
        )
        self._records.append(UsageRecord(
            timestamp=datetime.utcnow().isoformat(),
            model=model,
            feature=feature,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        ))
        return cost

    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self._records)

    def cost_by_feature(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for r in self._records:
            result[r.feature] = result.get(r.feature, 0.0) + r.cost_usd
        return result

    def summary(self) -> dict:
        return {
            "total_requests": len(self._records),
            "total_cost_usd": round(self.total_cost(), 6),
            "by_feature":     {k: round(v, 6) for k, v in self.cost_by_feature().items()},
        }
