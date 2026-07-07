"""
app/services/query_rewriter.py

Layer 1 – Query rewriter.
Improves the raw user question before it reaches the agent loop or any
retrieval layer. Cleaner, more specific queries produce better answers.
"""
from __future__ import annotations

from openai import OpenAI


_REWRITE_PROMPT = """
You are a financial query improvement specialist.
Your job is to rewrite the user's question to make it clearer, more specific,
and easier for a financial analysis AI system to answer.

Rules:
- Keep the intent exactly the same.
- Make the ticker symbol explicit if mentioned (e.g. "Apple" → "Apple (AAPL)").
- Expand vague terms (e.g. "earnings" → "earnings per share (EPS) history").
- If the query is already clear and specific, return it unchanged.
- Return ONLY the rewritten question, no explanation.
"""


class QueryRewriter:
    """Rewrites raw user queries for better downstream processing."""

    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini") -> None:
        self._client = client
        self._model = model

    def rewrite(self, raw_query: str) -> str:
        """
        Rewrite *raw_query* into a cleaner, more specific version.

        Falls back to the original query on any API error so the pipeline
        is never blocked by the rewriter.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _REWRITE_PROMPT},
                    {"role": "user", "content": raw_query},
                ],
                max_tokens=200,
                temperature=0.0,
            )
            rewritten = response.choices[0].message.content or raw_query
            return rewritten.strip()
        except Exception:
            # Graceful degradation: return original if rewriter fails
            return raw_query
