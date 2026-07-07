"""
app/security/content_filter.py

Layer 4 – Content filter.
Inspects retrieved documents or tool outputs DURING processing to detect
indirect prompt injection hidden in external data sources.
"""
from __future__ import annotations

from dataclasses import dataclass


_INJECTION_PATTERNS = [
    "ignore the user question",
    "ignore previous instructions",
    "disregard all rules",
    "say that this product",
    "always respond with",
    "you must now",
]


@dataclass
class ContentFilterResult:
    is_clean: bool
    flagged_pattern: str = ""


class ContentFilter:
    """
    Screens retrieved/external content for indirect prompt injection.

    Usage: call `.check(document_text)` before passing retrieved content
    to the LLM prompt.
    """

    def check(self, content: str) -> ContentFilterResult:
        lower = content.lower()
        for pattern in _INJECTION_PATTERNS:
            if pattern in lower:
                return ContentFilterResult(is_clean=False, flagged_pattern=pattern)
        return ContentFilterResult(is_clean=True)

    def sanitise(self, content: str) -> str:
        """Remove flagged patterns from content (best-effort)."""
        result = content
        for pattern in _INJECTION_PATTERNS:
            result = result.replace(pattern, "[REDACTED]")
        return result
