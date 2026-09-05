"""Gemma GGUF model server backed by SDK Gemma 4 agent semantics."""

from __future__ import annotations

import os
from typing import Any

from aicomp_sdk.agents.gemma4_agent import (
    DEFAULT_GEMMA4_MODEL_ID,
    Gemma4Agent,
    Gemma4ToolCallParser,
    _clean_fallback_assistant_text,
    _GEMMA4_TOOL_CALL_PATTERN,
    _parse_gemma4_arguments,
)
from aicomp_sdk.agents.hf_chat_template.response_parsing import (
    normalize_parsed_response,
    normalize_tool_arguments,
)
from aicomp_sdk.agents.hf_chat_template.types import HFGenerationResponse
from aicomp_sdk.agents.types import AgentDecision, JsonObject
from kaggle_evaluation.jed_attack_134815.gguf_model_server import (
    GgufModelServer,
    GgufModelSpec,
)


def _parse_gemma4_arguments_kaggle(args_blob: str) -> JsonObject:
    if args_blob.lstrip().startswith("{"):
        return normalize_tool_arguments(args_blob)
    return _parse_gemma4_arguments(args_blob)


class KaggleGemma4ToolCallParser(Gemma4ToolCallParser):
    def parse(
        self,
        response: HFGenerationResponse,
        *,
        fallback_call_id: str,
    ) -> AgentDecision:
        tool_calls = [
            {
                "type": "function",
                "function": {
                    "name": match.group("name"),
                    "arguments": _parse_gemma4_arguments_kaggle(
                        match.group("arguments")
                    ),
                },
            }
            for match in _GEMMA4_TOOL_CALL_PATTERN.finditer(response.raw_text)
        ]

        if not tool_calls:
            return super().parse(response, fallback_call_id=fallback_call_id)

        return normalize_parsed_response(
            {
                "role": "assistant",
                "content": _clean_fallback_assistant_text(response.text),
                "tool_calls": tool_calls,
            },
            fallback_call_id=fallback_call_id,
        )


SPEC = GgufModelSpec(
    model_label="Gemma",
    backend_label="gemma_4",
    model_id=DEFAULT_GEMMA4_MODEL_ID,
    repo_env_var="GEMMA_GGUF_REPO",
    file_env_var="GEMMA_GGUF_FILE",
    model_path_env_var="GEMMA_MODEL_PATH",
    default_repo="unsloth/gemma-4-26B-A4B-it-GGUF",
    default_file="gemma-4-26B-A4B-it-UD-Q4_K_M.gguf",
    create_agent=lambda backend: Gemma4Agent(
        backend,
        parser=KaggleGemma4ToolCallParser(),
    ),
)

_server = GgufModelServer(SPEC)


def predict(request: dict[str, Any]) -> dict[str, Any]:
    return _server.predict(request)


def _load_model() -> Any:
    return _server.load_model()


def _unload_model() -> None:
    _server.unload()


if __name__ == "__main__":
    import kaggle_evaluation.core.templates

    class GemmaModelInferenceServer(kaggle_evaluation.core.templates.InferenceServer):
        def __init__(self):
            super().__init__(predict)

    server = GemmaModelInferenceServer()
    if os.getenv("KAGGLE_IS_COMPETITION_RERUN"):
        server.serve()
    else:
        _load_model()
        print("Gemma model server ready for local testing.")
