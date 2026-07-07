"""
app/config.py

Centralised configuration for the Finteligence app.
All environment variables and model identifiers are read here once.
Other modules import from this file — never read os.getenv() directly.
"""
from __future__ import annotations

import os
import yaml
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)


def _load_yaml_config() -> dict:
    with open("config.yml", "r") as f:
        content = f.read()
    content = content.replace("${OPENAI_API_KEY}", os.getenv("OPENAI_API_KEY", ""))
    content = content.replace("${ALPHAVANTAGE_API_KEY}", os.getenv("ALPHAVANTAGE_API_KEY", ""))
    return yaml.safe_load(content)


_cfg = _load_yaml_config()

# ── API keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY:      str = _cfg["api_keys"]["OPENAI_API_KEY"]
ALPHAVANTAGE_API_KEY: str = os.getenv("ALPHAVANTAGE_API_KEY", "")

# ── Model identifiers ─────────────────────────────────────────────────────────
MODEL_CHAT:   str = "gpt-5.1"
MODEL_MINI:   str = "gpt-4o-mini"
MODEL_STT:    str = "whisper-1"
MODEL_TTS:    str = "gpt-4o-mini-tts"
TTS_VOICE:    str = "ash"

# ── Agent settings ────────────────────────────────────────────────────────────
AGENT_MAX_STEPS: int = 20

# ── Cache settings ────────────────────────────────────────────────────────────
SEMANTIC_CACHE_THRESHOLD: float = 0.92

# ── Security settings ─────────────────────────────────────────────────────────
INPUT_MAX_LENGTH: int = 2000

# ── Shared OpenAI client (singleton) ─────────────────────────────────────────
def get_openai_client() -> OpenAI:
    """Return a configured OpenAI client."""
    return OpenAI(api_key=OPENAI_API_KEY)
