import os
import json
import yaml
import streamlit as st
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv
from prompts import stronger_prompt
from tooling import handle_tool_calls, tools

# ── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Finteligence · AI Financial Analyst",
    page_icon=":material/candlestick_chart:",
    layout="centered",
    initial_sidebar_state="expanded",
)

load_dotenv(override=True)

# ── Config & client ──────────────────────────────────────────────────────────
with open("config.yml", "r") as f:
    content = f.read()
    secret_value = os.getenv("OPENAI_API_KEY")
    content = content.replace("${OPENAI_API_KEY}", secret_value)
    config = yaml.safe_load(content)

OPENAI_API_KEY = config["api_keys"]["OPENAI_API_KEY"]
client_openai = OpenAI(api_key=OPENAI_API_KEY)

MODEL_CHAT = "gpt-5.1"
MODEL_STT = "whisper-1"
MODEL_TTS = "gpt-4o-mini-tts"

# ── Suggestion chips ─────────────────────────────────────────────────────────
SUGGESTIONS = {
    ":blue[:material/candlestick_chart:] Analyze Apple (AAPL)": "Analyze Apple's latest income statement and give me the key financial insights.",
    ":green[:material/trending_up:] Microsoft free cash flow": "Retrieve Microsoft (MSFT) annual cash flow statement and compute the free cash flow trend.",
    ":violet[:material/query_stats:] Intrinsic value of NVDA": "Calculate the intrinsic value of NVIDIA (NVDA) and compare it with the current market price.",
    ":orange[:material/mic:] Earnings call insights": "What were the key highlights from Tesla's most recent earnings call?",
}

# ── Streaming helper ─────────────────────────────────────────────────────────
def stream_assistant_answer(client, model, conversation):
    """
    Stream the final assistant turn and return the full text.
    Uses st.write_stream with a generator for clean token-by-token display.
    """
    def _token_generator():
        stream = client.chat.completions.create(
            model=model,
            messages=conversation,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    return st.write_stream(_token_generator())


# ── Session state ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "## :material/candlestick_chart: Finteligence",
    )
    st.caption("Powered by financial intelligence")

    st.markdown("---")

    # ── Voice input ──────────────────────────────────────────────────────────
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

    # ── Capabilities ─────────────────────────────────────────────────────────
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

    # ── Clear chat ───────────────────────────────────────────────────────────
    if st.button(
        "Clear conversation",
        icon=":material/delete_sweep:",
        width="stretch",
    ):
        st.session_state.messages = []
        st.rerun()

    st.caption("Educational use only · Not investment advice")

# ── Main header ──────────────────────────────────────────────────────────────
st.title(":material/candlestick_chart: Finteligence")
st.caption(
    "Your AI-powered **fundamental analysis** mentor — ask about any publicly listed company."
)

# ── Suggestion chips (shown only on empty chat) ──────────────────────────────
if not st.session_state.messages:
    st.markdown("#### Try asking:")
    selected = st.pills(
        "Suggestions",
        list(SUGGESTIONS.keys()),
        label_visibility="collapsed",
    )
    if selected:
        st.session_state.messages.append(
            {"role": "user", "content": SUGGESTIONS[selected]}
        )
        st.rerun()

# ── Chat history ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    avatar = ":material/candlestick_chart:" if msg["role"] == "assistant" else None
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        audio_payload = msg.get("audio")
        if audio_payload:
            st.audio(audio_payload, format="audio/mp3")

# ── Input handling ───────────────────────────────────────────────────────────
user_prompt = None
user_display_content = None

if text_prompt := st.chat_input(
    placeholder="Ask about any stock, metric, or concept...",
    key="chat_input",
):
    user_prompt = text_prompt
    user_display_content = text_prompt

elif send_audio:
    if audio_value is not None:
        raw_audio = audio_value.getvalue()
        audio_file = BytesIO(raw_audio)
        audio_file.name = audio_value.name or "voice_message.wav"
        with st.spinner("Transcribing your voice message…"):
            transcription = client_openai.audio.transcriptions.create(
                model=MODEL_STT,
                file=audio_file,
            )
        user_prompt = transcription.text.strip()
        if user_prompt:
            user_display_content = f":material/mic: {user_prompt}"
        else:
            st.toast("Could not interpret the audio. Please try again.", icon=":material/warning:")
    else:
        st.toast("Record a voice message before sending.", icon=":material/info:")

# ── Agent loop ───────────────────────────────────────────────────────────────
if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_display_content or user_prompt)

    # Build conversation with system prompt prepended
    conversation = [{"role": "assistant", "content": stronger_prompt}]
    conversation.extend(
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    )

    # Tool-calling loop
    done = False
    while not done:
        completion = client_openai.chat.completions.create(
            model=MODEL_CHAT,
            messages=conversation,
            tools=tools,
        )
        choice = completion.choices[0]
        message = choice.message
        finish_reason = choice.finish_reason

        if finish_reason == "tool_calls" and message.tool_calls:
            tool_calls = message.tool_calls
            tool_calls_serialized = [
                {
                    "id": tc.id,
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    "type": tc.type,
                }
                for tc in tool_calls
            ]

            # Show a subtle status pill for each tool being called
            tool_names = [tc.function.name for tc in tool_calls]
            with st.status(f"Fetching data: {', '.join(tool_names)}…", expanded=False):
                results = handle_tool_calls(tool_calls)

            safe_content = message.content or ""
            if safe_content:
                st.session_state.messages.append({"role": message.role, "content": safe_content})
            conversation.append(
                {
                    "role": message.role,
                    "content": safe_content,
                    "tool_calls": tool_calls_serialized,
                }
            )
            conversation.extend(results)
            continue

        done = True

    # Stream the final response
    with st.chat_message("assistant", avatar=":material/candlestick_chart:"):
        response = stream_assistant_answer(
            client=client_openai,
            model=MODEL_CHAT,
            conversation=conversation,
        )

    st.session_state.messages.append({"role": "assistant", "content": response})

    # TTS audio generation
    audio_bytes = None
    with st.spinner("Generating audio response…"):
        try:
            speech = client_openai.audio.speech.create(
                model=MODEL_TTS, voice="ash", input=response
            )
            audio_bytes = speech.read()
        except Exception as exc:
            st.toast(f"Audio generation failed: {exc}", icon=":material/volume_off:")

    if audio_bytes:
        st.audio(
            audio_bytes,
            format="audio/mp3",
            start_time=0,
            autoplay=True,
            width="stretch",
        )
        # Persist audio in message history
        last_msg = st.session_state.messages[-1]
        if last_msg["role"] == "assistant":
            last_msg["audio"] = audio_bytes