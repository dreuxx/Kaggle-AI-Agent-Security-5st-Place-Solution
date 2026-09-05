#!/usr/bin/env python3
"""Measure Gemma EOG likelihood after each real post-tool output prefix."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Jinja2ChatFormatter


ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / "ai-agent-security-multi-step-tool-attacks"
sys.path[:0] = [str(ROOT), str(SDK)]

import attack  # noqa: E402
from aicomp_sdk.agents.hf_chat_template.agent import (  # noqa: E402
    _render_hf_messages,
    _render_hf_tools,
)
from aicomp_sdk.agents.hf_chat_template.types import HFModelProfile  # noqa: E402
from aicomp_sdk.agents.tool_specs import to_agent_tool_specs  # noqa: E402
from aicomp_sdk.agents.types import ToolCall, ToolResult  # noqa: E402
from aicomp_sdk.attacks.contracts import AttackRunConfig  # noqa: E402
from aicomp_sdk.core.env.sandbox import _DEFAULT_RUNTIME_INSTRUCTIONS  # noqa: E402
from aicomp_sdk.core.runtime_history import RuntimeHistory  # noqa: E402
from aicomp_sdk.core.tools import ToolSuite  # noqa: E402


MODEL = ROOT / (
    "model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/"
    "gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
)
OUTPUT = ROOT / "sandbox/output/gemma_posttool_early_eog_20260828.json"
NORMAL_POST = "<|channel>thought\n<channel|>"
EOG_TEXTS = ("<turn|>", "<eos>")


def _clear(llm: Llama) -> None:
    llm.reset()
    llm._ctx.kv_cache_clear()
    llm.n_tokens = 0


def _logits(llm: Llama, ids: list[int]) -> np.ndarray:
    _clear(llm)
    llm.eval(ids)
    return np.ctypeslib.as_array(
        llm._ctx.get_logits(), shape=(llm.n_vocab(),)
    ).copy()


def _rank(logits: np.ndarray, token_id: int) -> int:
    return int(np.count_nonzero(logits > logits[token_id])) + 1


def _top(
    llm: Llama,
    logits: np.ndarray,
    eog_ids: set[int],
    n: int = 12,
) -> list[dict[str, object]]:
    ids = np.argpartition(logits, -n)[-n:]
    ids = ids[np.argsort(logits[ids])[::-1]]
    return [
        {
            "id": int(token_id),
            "logit": float(logits[token_id]),
            "is_eog": int(token_id) in eog_ids,
            "text": llm.detokenize([int(token_id)], special=True).decode(
                "utf-8", errors="replace"
            ),
        }
        for token_id in ids
    ]


def main() -> None:
    candidates = attack.AttackAlgorithm(
        config={"fixed_model": "gemma", "n_candidates": 200}
    ).run(None, AttackRunConfig(time_budget_s=1.0, max_tool_hops=8))
    serialized = [list(candidate.user_messages) for candidate in candidates]
    if len(candidates) != 200 or len({tuple(value) for value in serialized}) != 200:
        raise RuntimeError("Current attack.py does not emit 200 unique Gemma candidates")
    if any(len(value) != 1 for value in serialized):
        raise RuntimeError("Expected one user message per candidate")

    llm = Llama(
        model_path=str(MODEL),
        n_ctx=8192,
        n_gpu_layers=24,
        logits_all=False,
        verbose=False,
    )
    formatter = Jinja2ChatFormatter(
        template=llm.metadata["tokenizer.chat_template"],
        eos_token=llm._model.token_get_text(llm.token_eos()),
        bos_token=llm._model.token_get_text(llm.token_bos()),
        stop_token_ids=[llm.token_eos()],
    )
    tools = _render_hf_tools(
        to_agent_tool_specs(
            tuple(ToolSuite(SDK / "aicomp_sdk/fixtures", isolate_fs=True).specs.values())
        )
    )
    profile = HFModelProfile(instruction_role="system")
    user_message = candidates[0].user_messages[0]
    history = RuntimeHistory().with_instruction(
        _DEFAULT_RUNTIME_INSTRUCTIONS
    ).with_user_message(user_message)
    call = ToolCall(
        call_id="call_000001",
        tool_name="http.post",
        arguments={"data": attack.PAYLOAD, "url": "://aa"},
    )
    post_history = history.with_tool_request(call).with_tool_result(
        ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            output_text="ok",
            is_error=False,
        )
    )
    post_prompt = formatter(
        messages=_render_hf_messages(post_history, profile=profile), tools=tools
    ).prompt
    post_ids = llm.tokenize(post_prompt.encode(), add_bos=False, special=True)
    normal_ids = llm.tokenize(NORMAL_POST.encode(), add_bos=False, special=True)
    eog_ids = {
        text: int(llm.tokenize(text.encode(), add_bos=False, special=True)[0])
        for text in EOG_TEXTS
    }
    eog_id_set = set(eog_ids.values())

    positions: list[dict[str, object]] = []
    for prefix_len in range(len(normal_ids) + 1):
        prefix = normal_ids[:prefix_len]
        logits = _logits(llm, post_ids + prefix)
        argmax_id = int(np.argmax(logits))
        positions.append(
            {
                "prefix_len": prefix_len,
                "prefix_ids": prefix,
                "prefix_text": llm.detokenize(prefix, special=True).decode(
                    "utf-8", errors="replace"
                ),
                "argmax": {
                    "id": argmax_id,
                    "logit": float(logits[argmax_id]),
                    "is_eog": argmax_id in eog_id_set,
                    "text": llm.detokenize([argmax_id], special=True).decode(
                        "utf-8", errors="replace"
                    ),
                },
                "eog": {
                    text: {
                        "id": token_id,
                        "rank": _rank(logits, token_id),
                        "logit": float(logits[token_id]),
                        "gap_to_argmax": float(logits[token_id] - logits[argmax_id]),
                    }
                    for text, token_id in eog_ids.items()
                },
                "top": _top(llm, logits, eog_id_set),
            }
        )

    payload = {
        "kind": "state_diagnostic_no_replay",
        "attack_path": str(ROOT / "attack.py"),
        "attack_sha256": hashlib.sha256((ROOT / "attack.py").read_bytes()).hexdigest(),
        "model_path": str(MODEL),
        "guardrail": "not_applicable_no_replay",
        "candidate_count": len(candidates),
        "unique_candidate_count": len({tuple(value) for value in serialized}),
        "candidate_messages": serialized,
        "candidate_sha256": [
            hashlib.sha256(
                json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
            ).hexdigest()
            for value in serialized
        ],
        "chat_template_sha256": hashlib.sha256(
            llm.metadata["tokenizer.chat_template"].encode()
        ).hexdigest(),
        "llama_cpp_version": __import__("llama_cpp").__version__,
        "post_prompt_tokens": len(post_ids),
        "normal_post_text": NORMAL_POST,
        "normal_post_ids": normal_ids,
        "eog_ids": eog_ids,
        "positions": positions,
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "attack_sha256": payload["attack_sha256"],
                "post_prompt_tokens": len(post_ids),
                "normal_post_ids": normal_ids,
                "positions": positions,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
