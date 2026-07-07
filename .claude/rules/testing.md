# Testing Rules

## When to Add Tests
When adding or changing any of the following, add or update tests:
- A prompt template or registry entry.
- A service (query rewriter, router, pipeline, cache).
- A security guard (input, content, output).
- An agent or tool.
- A routing decision or pipeline branch.

## Test Structure
- Mirror the source structure: `app/services/query_router.py` → `tests/test_routing.py`.
- One test file per major concern: `test_routing.py`, `test_security.py`, `test_tools.py`.
- Use `pytest` fixtures for shared setup (e.g. `InputGuard`, `QueryRouter`).

## Test Quality
- Test happy paths AND edge cases (empty input, very long input, unsafe input).
- Test that security guards block known bad inputs.
- Test that routing sends queries to the correct destination.
- Test that prompt registry raises `KeyError` on unknown tasks.
- Do NOT remove existing tests unless there is a documented reason.

## Running Tests
```bash
pytest tests/ -v
```
