"""
observability/tracer.py

Layer 6 - Request tracer.
Tracks the full journey of every user request through the pipeline so
that any bad answer can be debugged without guessing.

In production, swap the in-memory store for OpenTelemetry / Langfuse.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class Span:
    trace_id:  str
    name:      str
    start:     str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end:       str | None = None
    events:    list[dict[str, Any]] = field(default_factory=list)
    metadata:  dict[str, Any] = field(default_factory=dict)
    error:     bool = False
    cached:    bool = False
    blocked:   bool = False

    def log(self, event: str, **kwargs: Any) -> None:
        self.events.append({"event": event, "ts": datetime.utcnow().isoformat(), **kwargs})

    def finish(self, **kwargs: Any) -> None:
        self.end = datetime.utcnow().isoformat()
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Tracer:
    """
    Lightweight in-memory tracer.

    Each call to `start_span()` creates a new Span with a unique trace_id.
    Spans are stored in memory for the session and can be retrieved by trace_id.
    """

    def __init__(self) -> None:
        self._spans: dict[str, Span] = {}

    def start_span(self, name: str, **metadata: Any) -> Span:
        trace_id = str(uuid.uuid4())
        span = Span(trace_id=trace_id, name=name, metadata=metadata)
        self._spans[trace_id] = span
        return span

    def get_span(self, trace_id: str) -> Span | None:
        return self._spans.get(trace_id)

    def all_spans(self) -> list[Span]:
        return list(self._spans.values())

    def clear(self) -> None:
        self._spans.clear()
