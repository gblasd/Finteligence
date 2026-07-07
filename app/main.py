"""
app/main.py

Single entry-point for the Finteligence AI pipeline.

This file wires all 9 layers together and exposes two public interfaces:
  1. `create_pipeline()` — factory used by frontend/App.py (Streamlit UI).
  2. `run_query()`       — standalone CLI / test entry-point.

Nothing in this file contains AI logic. It only instantiates and connects
the layers defined in services/, agents/, prompts/, and security/.
"""
from __future__ import annotations

from app.config import get_openai_client
from app.models import PipelineInput, PipelineOutput
from app.services.pipeline import AIPipeline
from app.services.conversation import ConversationManager


def create_pipeline() -> tuple[AIPipeline, ConversationManager]:
    """
    Factory that wires all layers and returns a ready-to-use pipeline +
    a fresh conversation manager.

    Called once per Streamlit session via `@st.cache_resource`.
    """
    client       = get_openai_client()
    pipeline     = AIPipeline(client)
    conversation = ConversationManager()
    return pipeline, conversation


def run_query(user_message: str) -> PipelineOutput:
    """
    Convenience function for CLI usage or integration tests.

    Example
    -------
    >>> from app.main import run_query
    >>> result = run_query("What is Apple's FCF margin?")
    >>> print(result.response)
    """
    pipeline, conversation = create_pipeline()
    return pipeline.run(PipelineInput(user_message=user_message), conversation)


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "What is Apple's free cash flow margin?"
    result = run_query(query)
    print(result.response)
