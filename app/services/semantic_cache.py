"""
app/services/semantic_cache.py

Layer 1 - Semantic cache.
Avoids redundant model calls by returning a previously generated answer
when a new question is semantically equivalent to a past one.

This implementation uses in-memory storage with cosine similarity.
Swap `_store` for Redis + a vector DB for production.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from openai import OpenAI


@dataclass
class CacheEntry:
    query: str
    embedding: list[float]
    response: str


class SemanticCache:
    """
    In-memory semantic cache backed by OpenAI embeddings.

    Parameters
    ----------
    client    : Authenticated OpenAI client.
    threshold : Cosine similarity threshold above which a cache hit is declared.
    model     : Embedding model to use.
    """

    def __init__(
        self,
        client: OpenAI,
        threshold: float = 0.92,
        model: str = "text-embedding-3-small",
    ) -> None:
        self._client = client
        self._threshold = threshold
        self._model = model
        self._store: list[CacheEntry] = []

    def _embed(self, text: str) -> list[float]:
        response = self._client.embeddings.create(model=self._model, input=text)
        return response.data[0].embedding

    def _cosine(self, a: list[float], b: list[float]) -> float:
        na, nb = np.array(a), np.array(b)
        denom = np.linalg.norm(na) * np.linalg.norm(nb)
        return float(np.dot(na, nb) / denom) if denom else 0.0

    def get(self, query: str) -> str | None:
        """Return a cached response if a similar enough query exists."""
        if not self._store:
            return None
        try:
            emb = self._embed(query)
            best_score = max(self._cosine(emb, e.embedding) for e in self._store)
            if best_score >= self._threshold:
                for entry in self._store:
                    if self._cosine(emb, entry.embedding) == best_score:
                        return entry.response
        except Exception:
            pass
        return None

    def set(self, query: str, response: str) -> None:
        """Store a new query-response pair in the cache."""
        try:
            emb = self._embed(query)
            self._store.append(CacheEntry(query=query, embedding=emb, response=response))
        except Exception:
            pass

    def clear(self) -> None:
        """Flush all cached entries."""
        self._store.clear()
