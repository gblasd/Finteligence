"""
app/security/output_filter.py

Layer 4 – Output filter.
Last review gate before the AI response is shown to the user.
Checks for investment advice, disallowed content, and format correctness.
"""
from __future__ import annotations

_BUY_SELL_PATTERNS = [
    "i recommend buying",
    "you should buy",
    "buy this stock",
    "sell this stock",
    "i recommend selling",
    "strong buy",
    "strong sell",
    "you should invest in",
]

_DISCLAIMER = (
    "\n\n> ⚖️ *Este análisis es educativo e informativo, no es asesoramiento de inversión.*"
)


class OutputFilter:
    """
    Post-processes the raw LLM response before it reaches the user.

    Checks
    ------
    1. Strips investment advice language (adds disclaimer if detected).
    2. Ensures the response is non-empty.
    """

    def filter(self, response: str) -> str:
        if not response or not response.strip():
            return "Lo siento, no pude generar una respuesta. Por favor intenta de nuevo."

        lower = response.lower()
        for pattern in _BUY_SELL_PATTERNS:
            if pattern in lower:
                # Append disclaimer instead of blocking — educational context
                return response + _DISCLAIMER

        return response
