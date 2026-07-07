# Project Context — Finteligence

This is a production-ready AI financial analysis application built on the **9-layer architecture**.

## What the App Does
Finteligence is an AI-powered fundamental analysis mentor. Users can ask questions about
any publicly listed company (income statements, cash flows, intrinsic value, earnings calls)
and receive educational, structured answers.

## Technology Stack
- **LLM**: OpenAI GPT-5.1 (chat), Whisper (STT), GPT-4o-mini-TTS (TTS)
- **Data**: Alpha Vantage financial API
- **UI**: Streamlit
- **State**: Pydantic (Factor Agents pattern)

## 9-Layer Architecture

```
Finteligence/
├── app/
│   ├── main.py              ← Single entry-point for the pipeline
│   ├── config.py            ← Centralised configuration
│   ├── models.py            ← Shared Pydantic models
│   ├── services/            ← Layer 1: Brain (routing, rewriting, caching)
│   ├── agents/              ← Layer 2: Workers (financial agent + tools)
│   ├── prompts/             ← Layer 3: Prompt templates and registry
│   └── security/            ← Layer 4: Input/content/output guards
├── agent/                   ← Factor-Agents state machine (loop, state, tools)
├── evaluation/              ← Layer 5: Offline eval + online monitoring
├── observability/           ← Layer 6: Tracer, feedback, cost tracking
├── .antigravity/            ← Layer 7: AI assistant memory and rules
├── data/                    ← Layer 8: Raw, processed, and index data
├── tests/                   ← Layer 9: Automated test suite
├── App.py                   ← Streamlit UI (presentation only)
└── utils.py                 ← Financial data utilities (Alpha Vantage)
```

## Rules for AI Coding Assistants
- Do NOT place AI logic directly inside `App.py`.
- Always use the existing layer-based architecture.
- Prompts go in `app/prompts/` — never inline.
- Security checks are mandatory for every user input and AI output.
- Every new feature needs a test in `tests/`.
- See `.antigravity/rules/` for code style and testing standards.
