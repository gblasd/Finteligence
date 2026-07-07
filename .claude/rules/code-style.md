# Code Style Rules

## General
- Keep functions small, focused, and readable (single responsibility).
- Use type hints on every function signature and return type.
- Use meaningful names for services, agents, tools, and modules.
- Follow the 9-layer folder structure — do not place AI logic in `frontend/App.py` or `main.py`.

## Imports
- Use absolute imports from the project root.
- Group imports: stdlib → third-party → internal (separated by blank lines).
- Never use wildcard imports (`from module import *`).

## Prompts
- Do NOT hardcode prompt strings inside service or agent files.
- All prompts must be defined in `app/prompts/templates.py` and registered in `app/prompts/registry.py`.
- Reference prompts via `PromptRegistry.get(task)`.

## Security
- Every user input must pass through `app/security/input_guard.py` before reaching the agent.
- Every AI output must pass through `app/security/output_filter.py` before being shown.
- Never bypass the security layer for convenience.

## Error Handling
- All tool calls must be wrapped in try/except.
- Errors must be logged to the tracer, not silently swallowed.
- Fallback gracefully — never crash the UI on a tool failure.

## Testing
- Every new service, agent, or tool needs a corresponding test in `tests/`.
- Tests must be runnable with `pytest` from the project root.
