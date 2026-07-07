"""
app/security/input_guard.py

Layer 4 – Input guard.
Checks every user message BEFORE it enters the AI pipeline.
Catches prompt injection, out-of-scope requests, and oversized inputs.
"""
from __future__ import annotations

from dataclasses import dataclass


_MAX_LENGTH = 2000  # characters

_INJECTION_PATTERNS = [
    "ignore your instructions",
    "ignore previous instructions",
    "disregard your rules",
    "you are now",
    "act as",
    "pretend you are",
    "new persona",
    "jailbreak",
    "dan mode",
]

_OUT_OF_SCOPE_KEYWORDS = [
    "book a flight", "hotel price", "order food", "pizza delivery",
    "weather forecast", "bitcoin price", "crypto pump", "forex rate",
]


@dataclass
class GuardResult:
    is_safe: bool
    rejection_message: str = ""
    reason: str = ""


class InputGuard:
    """
    First line of defence against unsafe or invalid user input.

    Checks (in order)
    ------------------
    1. Input length limit.
    2. Prompt injection patterns.
    3. Out-of-scope keyword matching.
    """

    def check(self, text: str) -> GuardResult:
        # 1. Length check
        if len(text) > _MAX_LENGTH:
            return GuardResult(
                is_safe=False,
                reason="input_too_long",
                rejection_message=(
                    f"Tu mensaje es demasiado largo ({len(text)} caracteres). "
                    f"Por favor limítalo a {_MAX_LENGTH} caracteres."
                ),
            )

        lower = text.lower()

        # 2. Prompt injection detection
        for pattern in _INJECTION_PATTERNS:
            if pattern in lower:
                return GuardResult(
                    is_safe=False,
                    reason="prompt_injection",
                    rejection_message=(
                        "💡 Puedo ayudarte exclusivamente con **análisis fundamental**. "
                        "Esa solicitud no está permitida."
                    ),
                )

        # 3. Out-of-scope keywords
        for kw in _OUT_OF_SCOPE_KEYWORDS:
            if kw in lower:
                return GuardResult(
                    is_safe=False,
                    reason="out_of_scope",
                    rejection_message=(
                        "💡 Puedo ayudarte exclusivamente con **análisis fundamental y "
                        "educación financiera**. Esa solicitud está fuera de mi alcance."
                    ),
                )

        return GuardResult(is_safe=True)
