"""
observability/feedback.py

Layer 6 - Feedback collector.
Connects user feedback (helpful / not helpful) with the exact trace so
the team can understand and fix real failures instead of guessing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from evaluation.online_monitor import OnlineMonitor


@dataclass
class FeedbackRecord:
    trace_id:   str
    feedback:   str            # "helpful" | "not_helpful" | "wrong" | "report"
    query:      str = ""
    response:   str = ""
    timestamp:  str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class FeedbackCollector:
    """
    Records user feedback and ties it to the originating trace.

    When a user marks an answer "Not helpful", this collector stores the
    full context (query, response, trace) so developers can replay the
    exact request and improve the system.
    """

    def __init__(self) -> None:
        self._store: list[FeedbackRecord] = []
        self._monitor = OnlineMonitor()

    def record(self, trace_id: str, feedback: str, query: str = "", response: str = "") -> None:
        record = FeedbackRecord(
            trace_id=trace_id, feedback=feedback, query=query, response=response
        )
        self._store.append(record)
        self._monitor.record_feedback(trace_id, feedback)

    def get_negative(self) -> list[FeedbackRecord]:
        """Return all feedback records marked as negative."""
        return [r for r in self._store if r.feedback in ("not_helpful", "wrong", "report")]

    def all_records(self) -> list[FeedbackRecord]:
        return list(self._store)
