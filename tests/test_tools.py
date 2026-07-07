"""
tests/test_tools.py

Layer 9 – Tool and agent state tests.
Verifies the tool schema registry and agent state machine.
"""
import pytest
from agent.tools import TOOLS, TOOL_DISPLAY_NAMES
from agent.state import AgentState, AgentStatus
from agent.prompts import build_error_context
from app.prompts.registry import PromptRegistry


class TestToolRegistry:
    def test_all_tools_have_required_fields(self):
        for tool in TOOLS:
            assert "type" in tool
            assert "function" in tool
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

    def test_tool_display_names_cover_all_tools(self):
        tool_names = {t["function"]["name"] for t in TOOLS}
        assert tool_names == set(TOOL_DISPLAY_NAMES.keys())


class TestAgentState:
    def test_add_user_message(self):
        state = AgentState()
        state = state.add_user_message("Analyze AAPL")
        assert len(state.messages) == 1
        assert state.messages[0].role == "user"

    def test_status_transitions(self):
        state = AgentState()
        assert state.status == AgentStatus.IDLE
        state = state.with_status(AgentStatus.RUNNING)
        assert state.status == AgentStatus.RUNNING

    def test_serialise_roundtrip_strips_audio(self):
        state = AgentState()
        state = state.add_assistant_message("Test response")
        msgs = list(state.messages)
        msgs[-1] = msgs[-1].model_copy(update={"audio": bytes([0xFF, 0xFB])})
        state = state.model_copy(update={"messages": msgs})
        json_str = state.to_json()
        restored = AgentState.from_json(json_str)
        assert all(m.audio is None for m in restored.messages)

    def test_error_compaction(self):
        ctx = build_error_context(["APIError: rate limit", "ValueError: bad ticker"])
        assert "rate limit" in ctx
        assert "bad ticker" in ctx


class TestPromptRegistry:
    def test_get_known_task(self):
        prompt = PromptRegistry.get("financial_system")
        assert len(prompt) > 100

    def test_get_unknown_task_raises(self):
        with pytest.raises(KeyError):
            PromptRegistry.get("nonexistent_task")

    def test_register_new_prompt(self):
        PromptRegistry.register("test_task", "v1", "Test prompt content")
        assert PromptRegistry.get("test_task") == "Test prompt content"
