"""
evaluation/online_monitor.py

Layer 5 - Online monitor.
Tracks real-world usage patterns AFTER deployment: failure rates, invalid
outputs, low-confidence answers, and cost spikes.

In production, wire this to a database or monitoring service.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

_LOG_PATH = Path(__file__).parent / "eval_results" / "online_events.jsonl"


@dataclass
class MonitorEvent:
    event_type:  str                       # "response", "error", "block", "cache_hit"
    trace_id:    str
    timestamp:   str = field(default_factory=lambda: datetime.utcnow().isoformat())
    query:       str = ""
    category:    str = ""
    latency_ms:  float = 0.0
    cost_usd:    float = 0.0
    feedback:    str | None = None         # "helpful" | "not_helpful" | None
    notes:       str = ""


class OnlineMonitor:
    """Logs and aggregates real-time production events."""

    def __init__(self) -> None:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: MonitorEvent) -> None:
        """Append an event to the JSONL log."""
        with open(_LOG_PATH, "a") as f:
            f.write(json.dumps(asdict(event)) + "\n")

    def record_feedback(self, trace_id: str, feedback: str) -> None:
        """Record user feedback tied to a specific trace."""
        self.record(MonitorEvent(
            event_type="feedback",
            trace_id=trace_id,
            feedback=feedback,
        ))

    def summary(self) -> dict:
        """Return aggregate stats from the log."""
        if not _LOG_PATH.exists():
            return {"total_events": 0}
        events = []
        with open(_LOG_PATH) as f:
            for line in f:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        errors   = sum(1 for e in events if e.get("event_type") == "error")
        blocks   = sum(1 for e in events if e.get("event_type") == "block")
        feedback = [e for e in events if e.get("feedback")]
        return {
            "total_events":    len(events),
            "errors":          errors,
            "blocked":         blocks,
            "feedback_count":  len(feedback),
            "avg_latency_ms":  (
                sum(e.get("latency_ms", 0) for e in events) / len(events)
                if events else 0
            ),
        }
