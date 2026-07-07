# Agent Rules — Finteligence

This document defines how agents must be built and behave in this project.

## General Principles (Factor Agents)
1. **Small and focused**: each agent has one clear responsibility.
2. **Stateless reducers**: `step(state) → next_state` — no global mutation.
3. **Own the control flow**: explicit `max_steps` cap to prevent runaway loops.
4. **Compact errors into context**: tool failures are injected into the context window, not silently dropped.
5. **Channel-agnostic**: agents are invoked via `FinteligenceRunner`, not directly from the UI.

## Agent Inventory

| Agent | File | Responsibility |
|---|---|---|
| FinancialAgent | `app/agents/financial_agent.py` | Core reasoning loop for financial analysis |
| QueryDecomposer | `app/agents/query_decomposer.py` | Breaks complex queries into sub-questions |
| AdaptiveRouter | `app/agents/adaptive_router.py` | Smart traffic controller for routing |

## Tool Rules
- Tools live in `app/agents/tools/`.
- Each tool wraps a function from `utils.py` and adds logging.
- Tools must return structured data (dict or list).
- Tools must handle exceptions and never crash the agent loop.
- Tool schemas are defined in `agent/tools.py` — schemas and implementations are separate.

## Adding a New Agent
1. Create `app/agents/my_agent.py` with a single public `run()` method.
2. If the agent uses tools, add the tool schema to `agent/tools.py` and the implementation to `app/agents/tools/`.
3. Register the agent in `app/services/pipeline.py` if it's part of the main flow.
4. Add tests in `tests/test_agents.py`.
5. Update this file.
