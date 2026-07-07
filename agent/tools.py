"""
agent/tools.py

Factor 1 - Natural language to tool calls (schema registry).
Factor 4 - Tools are just structured outputs.
============================================================
This module is the single source of truth for:
  • Tool JSON schemas consumed by the OpenAI function-calling API.
  • The ordered `TOOLS` list passed to every chat completion request.

Nothing here executes any business logic — schemas are pure data.
The actual implementations live in `tool_handlers.py` so that:
  • Schemas can be loaded / validated without importing heavy dependencies.
  • Adding a new tool requires touching exactly two files: this one
    (schema) and `tool_handlers.py` (implementation).
"""

from __future__ import annotations

# Individual tool schemas

GET_INTRINSIC_VALUE: dict = {
    "name": "get_intrinsic_value",
    "description": (
        "Usa esta herramienta para obtener el valor intrínseco de la compañía solicitada. "
        "Evita cálculos ajenos a la herramienta proporcionada como WACC o DFC. "
        "Contrasta siempre con el precio actual para dar insights sin ser recomendación de "
        "compra o venta."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "El TICKER de la compañía a analizar (ej. AAPL, MSFT).",
            }
        },
        "required": ["ticker"],
        "additionalProperties": False,
    },
}

GET_INCOME_STATEMENT: dict = {
    "name": "get_income_statement",
    "description": (
        "Usa esta herramienta para obtener datos del estado de resultados de la compañía "
        "solicitada por el usuario."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "El TICKER de la compañía a analizar.",
            },
            "period": {
                "type": "string",
                "enum": ["anual", "trimestral"],
                "description": "Periodo del reporte: anual o trimestral.",
            },
        },
        "required": ["ticker", "period"],
        "additionalProperties": False,
    },
}

GET_BALANCE_SHEET: dict = {
    "name": "get_balance_sheet",
    "description": (
        "Usa esta herramienta para obtener datos del balance general de la compañía solicitada."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "El TICKER de la compañía a analizar.",
            },
            "period": {
                "type": "string",
                "enum": ["anual", "trimestral"],
                "description": "Periodo del reporte: anual o trimestral.",
            },
        },
        "required": ["ticker", "period"],
        "additionalProperties": False,
    },
}

GET_CASHFLOW_STATEMENT: dict = {
    "name": "get_cashflow_statement",
    "description": (
        "Usa esta herramienta para obtener datos del flujo de efectivo de la compañía solicitada."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "El TICKER de la compañía a analizar.",
            },
            "period": {
                "type": "string",
                "enum": ["anual", "trimestral"],
                "description": "Periodo del reporte: anual o trimestral.",
            },
        },
        "required": ["ticker", "period"],
        "additionalProperties": False,
    },
}

GET_EARNINGS: dict = {
    "name": "get_earnings",
    "description": (
        "Usa esta herramienta para obtener datos de ganancias por acción (EPS) de la compañía "
        "solicitada."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "El TICKER de la compañía a analizar.",
            },
            "period": {
                "type": "string",
                "enum": ["anual", "trimestral"],
                "description": "Periodo del reporte: anual o trimestral.",
            },
        },
        "required": ["ticker", "period"],
        "additionalProperties": False,
    },
}

GET_CALL_TRANSCRIPTS: dict = {
    "name": "get_call_transcripts",
    "description": (
        "Usa esta herramienta para obtener insights clave de una transcripción de earnings call "
        "de la compañía solicitada."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "El TICKER de la compañía a analizar.",
            },
            "quarter": {
                "type": "string",
                "description": (
                    "El trimestre de la llamada con inversionistas (ej. '2024Q1', '2023Q4')."
                ),
            },
        },
        "required": ["ticker", "quarter"],
        "additionalProperties": False,
    },
}

# Ordered tool registry (passed to every chat completion)

TOOLS: list[dict] = [
    {"type": "function", "function": GET_INTRINSIC_VALUE},
    {"type": "function", "function": GET_INCOME_STATEMENT},
    {"type": "function", "function": GET_BALANCE_SHEET},
    {"type": "function", "function": GET_CASHFLOW_STATEMENT},
    {"type": "function", "function": GET_EARNINGS},
    {"type": "function", "function": GET_CALL_TRANSCRIPTS},
]

# Helper: tool names for UI display

TOOL_DISPLAY_NAMES: dict[str, str] = {
    "get_intrinsic_value":    "Intrinsic Value",
    "get_income_statement":   "Income Statement",
    "get_balance_sheet":      "Balance Sheet",
    "get_cashflow_statement": "Cash Flow Statement",
    "get_earnings":           "Earnings (EPS)",
    "get_call_transcripts":   "Earnings Call Transcripts",
}
