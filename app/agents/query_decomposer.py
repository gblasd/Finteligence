"""
app/agents/query_decomposer.py

Layer 2 - Query decomposer agent.
Breaks a complex multi-part financial question into ordered sub-questions
that the financial agent can answer one by one.
"""
from __future__ import annotations

import json
from openai import OpenAI


_DECOMPOSE_PROMPT = """
You are a financial research analyst. Break the following complex financial question
into 2-4 clear, self-contained sub-questions that together fully answer the original.

Return a JSON array of strings. Example:
["What is AAPL's revenue trend over 5 years?", "What is AAPL's FCF margin?"]

Return ONLY the JSON array, no explanation.
"""


class QueryDecomposer:
    """Decomposes complex financial queries into ordered sub-questions."""

    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini") -> None:
        self._client = client
        self._model  = model

    def decompose(self, query: str) -> list[str]:
        """
        Return a list of sub-questions for *query*.
        Falls back to [query] if decomposition fails.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _DECOMPOSE_PROMPT},
                    {"role": "user",   "content": query},
                ],
                temperature=0.0,
                max_tokens=400,
            )
            raw = response.choices[0].message.content or ""
            parts = json.loads(raw)
            if isinstance(parts, list) and all(isinstance(p, str) for p in parts):
                return parts
        except Exception:
            pass
        return [query]
