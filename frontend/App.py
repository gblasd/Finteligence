"""
App.py — Finteligence Streamlit UI

Presentation layer ONLY.
All AI logic is handled by app/main.py and the 9-layer architecture below it.
This file only renders the UI and passes user input to the pipeline.
"""
from __future__ import annotations

import os
import sys

# Ensure root directory is in python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st
from app.main import create_pipeline
from app.models import PipelineInput
from agent.state import AgentStatus
from agent.tools import TOOL_DISPLAY_NAMES
from observability.feedback import FeedbackCollector

# Page config (must be first Streamlit call)
st.set_page_config(
    page_title="Finteligence · AI Financial Analyst",
    page_icon=":material/candlestick_chart:",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Pipeline (cached per session — Layer 1 wired via app/main.py)
@st.cache_resource
def _get_pipeline():
    with st.spinner("Loading AI pipeline..."):
        pipeline, conversation = create_pipeline()
    return pipeline, conversation

pipeline, conversation = _get_pipeline()
feedback_collector = FeedbackCollector()

# Suggestion chips
SUGGESTIONS = {
    ":blue[:material/candlestick_chart:] Analyze Apple (AAPL)": (
        "Analyze Apple's latest income statement and give me the key financial insights."
    ),
    ":green[:material/trending_up:] Microsoft free cash flow": (
        "Retrieve Microsoft (MSFT) annual cash flow statement and compute the free cash flow trend."
    ),
    ":violet[:material/query_stats:] Intrinsic value of NVDA": (
        "Calculate the intrinsic value of NVIDIA (NVDA) and compare it with the current market price."
    ),
    ":orange[:material/mic:] Earnings call insights": (
        "What were the key highlights from Tesla's most recent earnings call?"
    ),
}

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # list of {"role", "content", "audio", "trace_id"}

# TTS helper
def _generate_audio(text: str) -> bytes | None:
    from app.config import get_openai_client, MODEL_TTS, TTS_VOICE
    try:
        client = get_openai_client()
        speech = client.audio.speech.create(model=MODEL_TTS, voice=TTS_VOICE, input=text)
        return speech.read()
    except Exception:
        return None

# STT helper
def _transcribe(audio_bytes: bytes, filename: str = "voice.wav") -> str:
    from io import BytesIO
    from app.config import get_openai_client, MODEL_STT
    buf = BytesIO(audio_bytes)
    buf.name = filename
    client = get_openai_client()
    return client.audio.transcriptions.create(model=MODEL_STT, file=buf).text.strip()

# Sidebar
with st.sidebar:
    st.markdown("## :material/candlestick_chart: Finteligence")
    st.caption("Powered by financial intelligence")
    st.markdown("---")

    st.subheader(":material/mic: Voice input", divider=False)
    st.caption("Record a voice message and click **Send audio** to transcribe it.")
    audio_value = st.audio_input("Record a message", label_visibility="collapsed")
    send_audio = st.button(
        "Send audio", key="send_audio_button",
        icon=":material/send:", type="primary", width="stretch",
    )

    st.markdown("---")

    st.subheader(":material/database: Available data", divider=False)
    for icon, label in [
        (":material/receipt_long:", "Income statement"),
        (":material/balance:", "Balance sheet"),
        (":material/waterfall_chart:", "Cash flow statement"),
        (":material/bar_chart:", "EPS & earnings"),
        (":material/record_voice_over:", "Earnings call transcripts"),
        (":material/calculate:", "Intrinsic value"),
    ]:
        st.markdown(f"{icon} {label}")

    st.markdown("---")

    if st.button("Clear conversation", icon=":material/delete_sweep:", width="stretch"):
        st.session_state.chat_history = []
        conversation.clear()
        st.rerun()

    st.caption("Educational use only · Not investment advice")

# Main header
st.title(":material/candlestick_chart: Finteligence")
st.caption(
    "Your AI-powered **fundamental analysis** mentor — ask about any publicly listed company."
)

# Suggestion chips (empty chat only)
if not st.session_state.chat_history:
    st.markdown("#### Try asking:")
    selected = st.pills("Suggestions", list(SUGGESTIONS.keys()), label_visibility="collapsed")
    if selected:
        user_prompt = SUGGESTIONS[selected]
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        st.rerun()

# Chat history
for msg in st.session_state.chat_history:
    avatar = ":material/candlestick_chart:" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("content"):
            st.markdown(msg["content"])
        if msg.get("audio"):
            st.audio(msg["audio"], format="audio/mp3")

# Input handling
user_prompt: str | None = None
user_display: str | None = None

if text_prompt := st.chat_input(
    placeholder="Ask about any stock, metric, or concept...",
    key="chat_input",
):
    user_prompt = text_prompt
    user_display = text_prompt

elif send_audio:
    if audio_value is not None:
        with st.spinner("Transcribing your voice message…"):
            user_prompt = _transcribe(
                audio_value.getvalue(),
                filename=getattr(audio_value, "name", None) or "voice.wav",
            )
        if user_prompt:
            user_display = f":material/mic: {user_prompt}"
        else:
            st.toast("Could not interpret the audio. Please try again.", icon=":material/warning:")
    else:
        st.toast("Record a voice message before sending.", icon=":material/info:")

# Pipeline execution
if user_prompt:
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_display or user_prompt)

    with st.chat_message("assistant", avatar=":material/candlestick_chart:"):
        with st.spinner("Thinking…"):
            result = pipeline.run(PipelineInput(user_message=user_prompt), conversation)

        if result.blocked:
            st.warning(result.response, icon=":material/security:")
        else:
            st.markdown(result.response)

    # TTS
    audio_bytes: bytes | None = None
    if not result.blocked and result.response:
        with st.spinner("Generating audio response…"):
            audio_bytes = _generate_audio(result.response)

        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3", start_time=0, autoplay=True)

    # Feedback buttons (Layer 6 — observability/feedback.py)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Helpful", key=f"helpful_{len(st.session_state.chat_history)}"):
            feedback_collector.record(result.trace_id, "helpful", user_prompt, result.response)
            st.toast("Thank you for your feedback!", icon=":material/thumb_up:")
    with col2:
        if st.button("👎 Not helpful", key=f"not_helpful_{len(st.session_state.chat_history)}"):
            feedback_collector.record(result.trace_id, "not_helpful", user_prompt, result.response)
            st.toast("Feedback recorded. We'll work to improve.", icon=":material/thumb_down:")

    # Persist to chat history
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": result.response,
        "audio": audio_bytes,
        "trace_id": result.trace_id,
    })