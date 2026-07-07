"""
App.py — Finteligence Streamlit UI

Factor 11 - Trigger from anywhere (channel-agnostic).
============================================================
This file is the *presentation layer only*.

Responsibilities
----------------
• Render the Streamlit UI (sidebar, chat history, input widgets).
• Convert UI events (text input, audio recording) into calls on
  `FinteligenceRunner`.
• Display intermediate tool-call statuses via the `on_step` callback.
• Stream the final assistant answer.

What this file does NOT contain
--------------------------------
• Any OpenAI API calls beyond TTS/STT delegation to the runner.
• Any business logic (financial calculations, tool dispatch).
• Any prompt strings.
• Any agent control flow.
"""

import streamlit as st
from agent.runner import FinteligenceRunner
from agent.state import AgentState, AgentStatus
from agent.tools import TOOL_DISPLAY_NAMES

# Page config (must be first Streamlit call)
st.set_page_config(
    page_title="Finteligence · AI Financial Analyst",
    page_icon=":material/candlestick_chart:",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Runner (Factor 11: trigger from anywhere)
# The runner is cached so it is instantiated once per Streamlit session.
@st.cache_resource
def get_runner() -> FinteligenceRunner:
    return FinteligenceRunner()

runner = get_runner()

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

# Session state (Factor 5: single source of truth via AgentState)
# We persist the full AgentState in Streamlit's session_state as a JSON string
# so that the runner can resume across reruns without losing context.
if "agent_state_json" not in st.session_state:
    st.session_state.agent_state_json = AgentState().to_json()


def _get_state() -> AgentState:
    return AgentState.from_json(st.session_state.agent_state_json)


def _save_state(state: AgentState) -> None:
    st.session_state.agent_state_json = state.to_json()


# Streaming helper

def _stream_final_response(state: AgentState) -> str:
    """
    Stream the final assistant message token-by-token using st.write_stream.

    We re-stream from the runner's client to get token-by-token output.
    The final accumulated text is returned for persistence.
    """
    from agent.prompts import SYSTEM_PROMPT
    from openai import OpenAI
    import os, yaml
    from dotenv import load_dotenv

    load_dotenv(override=True)
    with open("config.yml") as f:
        content = f.read().replace("${OPENAI_API_KEY}", os.getenv("OPENAI_API_KEY", ""))
    config = yaml.safe_load(content)
    client = OpenAI(api_key=config["api_keys"]["OPENAI_API_KEY"])

    def _token_gen():
        stream = client.chat.completions.create(
            model=runner.model_chat,
            messages=state.api_messages(SYSTEM_PROMPT),
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    return st.write_stream(_token_gen())


# Sidebar
with st.sidebar:
    st.markdown("## :material/candlestick_chart: Finteligence")
    st.caption("Powered by financial intelligence")
    st.markdown("---")

    # Voice input (Factor 7: human contact as first-class interaction)
    st.subheader(":material/mic: Voice input", divider=False)
    st.caption("Record a voice message and click **Send audio** to transcribe it.")
    audio_value = st.audio_input("Record a message", label_visibility="collapsed")
    send_audio = st.button(
        "Send audio",
        key="send_audio_button",
        icon=":material/send:",
        type="primary",
        width="stretch",
    )

    st.markdown("---")

    # Capabilities
    st.subheader(":material/database: Available data", divider=False)
    capabilities = [
        (":material/receipt_long:", "Income statement"),
        (":material/balance:", "Balance sheet"),
        (":material/waterfall_chart:", "Cash flow statement"),
        (":material/bar_chart:", "EPS & earnings"),
        (":material/record_voice_over:", "Earnings call transcripts"),
        (":material/calculate:", "Intrinsic value"),
    ]
    for icon, label in capabilities:
        st.markdown(f"{icon} {label}")

    st.markdown("---")

    # Clear chat
    if st.button(
        "Clear conversation",
        icon=":material/delete_sweep:",
        width="stretch",
    ):
        _save_state(AgentState())
        st.rerun()

    st.caption("Educational use only · Not investment advice")

# Main header
st.title(":material/candlestick_chart: Finteligence")
st.caption(
    "Your AI-powered **fundamental analysis** mentor — ask about any publicly listed company."
)

# Suggestion chips (empty chat only)
current_state = _get_state()
if not current_state.messages:
    st.markdown("#### Try asking:")
    selected = st.pills(
        "Suggestions",
        list(SUGGESTIONS.keys()),
        label_visibility="collapsed",
    )
    if selected:
        user_prompt = SUGGESTIONS[selected]
        current_state = current_state.add_user_message(user_prompt)
        _save_state(current_state)
        st.rerun()

# Chat history
for msg in current_state.messages:
    if msg.role not in ("user", "assistant"):
        continue  # Skip tool / system messages from the display
    avatar = ":material/candlestick_chart:" if msg.role == "assistant" else None
    with st.chat_message(msg.role, avatar=avatar):
        if msg.content:
            st.markdown(msg.content)
        if msg.audio:
            st.audio(msg.audio, format="audio/mp3")

# Input handling
user_prompt: str | None = None
user_display_content: str | None = None

if text_prompt := st.chat_input(
    placeholder="Ask about any stock, metric, or concept...",
    key="chat_input",
):
    user_prompt = text_prompt
    user_display_content = text_prompt

elif send_audio:
    if audio_value is not None:
        raw_audio = audio_value.getvalue()
        audio_file_name = getattr(audio_value, "name", None) or "voice_message.wav"
        with st.spinner("Transcribing your voice message…"):
            user_prompt = runner.transcribe_audio(raw_audio, filename=audio_file_name)
        if user_prompt:
            user_display_content = f":material/mic: {user_prompt}"
        else:
            st.toast("Could not interpret the audio. Please try again.", icon=":material/warning:")
    else:
        st.toast("Record a voice message before sending.", icon=":material/info:")

# Agent loop
if user_prompt:
    current_state = _get_state()

    # Show the user's message immediately
    with st.chat_message("user"):
        st.markdown(user_display_content or user_prompt)

    # on_step callback: show a status indicator per tool call
    _status_placeholder = st.empty()

    def _on_step(state: AgentState) -> None:
        """Called after each step in the agent loop — used for UI feedback."""
        if state.status == AgentStatus.AWAITING_TOOL:
            # Collect names from the last assistant message's tool_calls
            for msg in reversed(state.messages):
                if msg.role == "assistant" and msg.tool_calls:
                    display_names = [
                        TOOL_DISPLAY_NAMES.get(tc["function"]["name"], tc["function"]["name"])
                        for tc in msg.tool_calls
                    ]
                    _status_placeholder.status(
                        f"Fetching data: {', '.join(display_names)}…",
                        expanded=False,
                    )
                    break

    # Run the agent (Factor 8: runner owns control flow)
    final_state = runner.run_turn(
        state=current_state,
        user_message=user_prompt,
        on_step=_on_step,
    )
    _status_placeholder.empty()

    # Stream the final answer
    with st.chat_message("assistant", avatar=":material/candlestick_chart:"):
        if final_state.status == AgentStatus.ERROR:
            st.error(
                f"Something went wrong: {final_state.last_error}",
                icon=":material/error:",
            )
        else:
            streamed_response = _stream_final_response(final_state)
            # Update last_response with the streamed text
            final_state = final_state.model_copy(update={"last_response": streamed_response})

    # TTS
    if final_state.status == AgentStatus.DONE and final_state.last_response:
        audio_bytes: bytes | None = None
        with st.spinner("Generating audio response…"):
            audio_bytes = runner.generate_audio(final_state.last_response)

        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3", start_time=0, autoplay=True)
            # Attach audio to the last assistant message for replay in history
            msgs = list(final_state.messages)
            for i in range(len(msgs) - 1, -1, -1):
                if msgs[i].role == "assistant":
                    msgs[i] = msgs[i].model_copy(update={"audio": audio_bytes})
                    break
            final_state = final_state.model_copy(update={"messages": msgs})

    # Persist the updated state
    _save_state(final_state)