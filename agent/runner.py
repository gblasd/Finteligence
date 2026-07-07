"""
agent/runner.py

Factor 6  - Launch / Pause / Resume with simple APIs.
Factor 11 - Trigger from anywhere (channel-agnostic).
============================================================
`FintelligenceRunner` is the public API surface for the agent.

Design goals
------------
• Channel-agnostic: the runner knows nothing about Streamlit, HTTP, or
  CLI. It can be driven from any interface that can call a Python method.
• Simple lifecycle: `run_turn()` is the only method a caller needs for
  the standard flow.
• Pause / resume: the full state can be exported via `export_state()` and
  restored via `import_state()`, enabling seamless persistence (e.g.
  storing state in st.session_state or a database between requests).
• TTS is handled here as a *post-processing* step so the loop stays pure
  (Factor 10 - small, focused responsibility per layer).

Factor 7 - Human interaction as a first-class tool:
  Audio transcription (STT) is exposed via `transcribe_audio()` so any
  channel (voice, web, API) can feed a user utterance into the same loop.
"""

from __future__ import annotations

import os
from io import BytesIO
from typing import Callable

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from .state import AgentState, AgentStatus
from .loop import run as _run
from .prompts import SYSTEM_PROMPT

load_dotenv(override=True)


def _load_client() -> OpenAI:
    """Build the OpenAI client from environment / config."""
    with open("config.yml", "r") as f:
        content = f.read().replace(
            "${OPENAI_API_KEY}", os.getenv("OPENAI_API_KEY", "")
        )
    config = yaml.safe_load(content)
    api_key = config["api_keys"]["OPENAI_API_KEY"]
    return OpenAI(api_key=api_key)


class FinteligenceRunner:
    """
    Channel-agnostic entry-point for the Finteligence agent (Factor 11).

    Usage (Streamlit)
    -----------------
    >>> runner = FinteligenceRunner()
    >>> state = runner.run_turn(state, user_message="Analyze AAPL")
    >>> print(state.last_response)

    Usage (CLI / test)
    ------------------
    >>> runner = FinteligenceRunner()
    >>> state = AgentState()
    >>> state = runner.run_turn(state, user_message="What is the FCF margin of MSFT?")
    """

    def __init__(
        self,
        model_chat: str = "gpt-5.1",
        model_stt: str = "whisper-1",
        model_tts: str = "gpt-4o-mini-tts",
        tts_voice: str = "ash",
        system_prompt: str = SYSTEM_PROMPT,
        max_steps: int = 20,
    ) -> None:
        self.client = _load_client()
        self.model_chat = model_chat
        self.model_stt = model_stt
        self.model_tts = model_tts
        self.tts_voice = tts_voice
        self.system_prompt = system_prompt
        self.max_steps = max_steps

    # Core turn execution

    def run_turn(
        self,
        state: AgentState,
        user_message: str,
        on_step: Callable[[AgentState], None] | None = None,
    ) -> AgentState:
        """
        Factor 6 - Simple API for launching a turn.

        Append `user_message` to the state and drive the agent loop
        until the model produces a final answer.

        Parameters
        ----------
        state        : Current AgentState (empty for a fresh conversation).
        user_message : The raw text of the user's message.
        on_step      : Optional callback for each intermediate state
                       (e.g. to show a Streamlit spinner per tool call).

        Returns
        -------
        Updated AgentState with `last_response` populated.
        """
        state = state.add_user_message(user_message)
        return _run(
            state=state,
            client=self.client,
            model=self.model_chat,
            system_prompt=self.system_prompt,
            max_steps=self.max_steps,
            on_step=on_step,
        )

    # TTS

    def generate_audio(self, text: str) -> bytes | None:
        """
        Convert text to speech and return raw MP3 bytes.
        Returns None on failure (non-critical path).
        """
        try:
            speech = self.client.audio.speech.create(
                model=self.model_tts,
                voice=self.tts_voice,
                input=text,
            )
            return speech.read()
        except Exception:
            return None

    # STT (Factor 7 – Human contact via tool)

    def transcribe_audio(self, audio_bytes: bytes, filename: str = "voice.wav") -> str:
        """
        Transcribe audio bytes to text using Whisper.

        This is exposed as a first-class method so any channel (web form,
        REST endpoint, CLI) can feed voice input into `run_turn()` without
        duplicating transcription logic.
        """
        buf = BytesIO(audio_bytes)
        buf.name = filename
        transcription = self.client.audio.transcriptions.create(
            model=self.model_stt,
            file=buf,
        )
        return transcription.text.strip()

    # State persistence (Factor 6 – Pause / Resume)

    def export_state(self, state: AgentState) -> str:
        """Serialise the full conversation state to a JSON string."""
        return state.to_json()

    def import_state(self, raw_json: str) -> AgentState:
        """Restore a previously exported state (e.g. from st.session_state)."""
        return AgentState.from_json(raw_json)
