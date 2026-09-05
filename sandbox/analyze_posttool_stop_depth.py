#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


MODELS = {
    "gpt_oss": ROOT / (
        "model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/"
        "gpt-oss-20b-Q4_K_M.gguf"
    ),
    "gemma": ROOT / (
        "model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/"
        "gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
    ),
}
OBSERVED_OUTPUT = {
    "gpt_oss": "<|channel|>final<|message|>",
    "gemma": "<|channel>thought\n<channel|>",
}


def _top(llm: Llama, logits: np.ndarray, n: int = 8) -> list[dict[str, object]]:
    ids = np.argpartition(logits, -n)[-n:]
    ids = ids[np.argsort(logits[ids])[::-1]]
    return [
        {
            "id": int(token_id),
            "logit": float(logits[token_id]),
            "text": llm.detokenize([int(token_id)], special=True).decode(
                "utf-8", errors="replace"
            ),
        }
        for token_id in ids
    ]


def _rank(logits: np.ndarray, token_id: int) -> int:
    return int(np.count_nonzero(logits > logits[token_id])) + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=tuple(MODELS))
    parser.add_argument("--n-gpu-layers", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    llm = Llama(
        model_path=str(MODELS[args.model]),
        n_ctx=8192,
        n_gpu_layers=args.n_gpu_layers,
        logits_all=False,
        verbose=False,
    )
    eos_id = llm.token_eos()
    formatter = Jinja2ChatFormatter(
        template=llm.metadata["tokenizer.chat_template"],
        eos_token=llm._model.token_get_text(eos_id),
        bos_token=llm._model.token_get_text(llm.token_bos()),
        stop_token_ids=[eos_id],
    )
    tools = _render_hf_tools(
        to_agent_tool_specs(tuple(ToolSuite(SDK / "aicomp_sdk/fixtures", isolate_fs=True).specs.values()))
    )
    profile = HFModelProfile(instruction_role="system")
    candidates = attack.AttackAlgorithm(
        config={"fixed_model": args.model, "n_candidates": 200}
    ).run(None, AttackRunConfig(time_budget_s=1.0, max_tool_hops=8))
    user_message = candidates[0].user_messages[0]
    url = "http://aa" if args.model == "gpt_oss" else "://aa"
    history = (
        RuntimeHistory()
        .with_instruction(_DEFAULT_RUNTIME_INSTRUCTIONS)
        .with_user_message(user_message)
    )
    call = ToolCall(
        call_id="call_000001",
        tool_name="http.post",
        arguments={"data": attack.PAYLOAD, "url": url},
    )
    post_history = history.with_tool_request(call).with_tool_result(
        ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            output_text="ok",
            is_error=False,
        )
    )
    rendered_messages = _render_hf_messages(post_history, profile=profile)
    prompt = formatter(messages=rendered_messages, tools=tools).prompt
    prompt_ids = llm.tokenize(prompt.encode(), add_bos=False, special=True)
    output_text = OBSERVED_OUTPUT[args.model]
    output_ids = llm.tokenize(output_text.encode(), add_bos=False, special=True)

    llm.reset()
    llm.eval(prompt_ids)
    steps: list[dict[str, object]] = []
    prefix: list[int] = []
    for depth in range(len(output_ids) + 1):
        logits = np.ctypeslib.as_array(
            llm._ctx.get_logits(), shape=(llm.n_vocab(),)
        ).copy()
        expected_id = output_ids[depth] if depth < len(output_ids) else eos_id
        steps.append(
            {
                "depth": depth,
                "prefix_ids": list(prefix),
                "prefix_text": llm.detokenize(prefix, special=True).decode(
                    "utf-8", errors="replace"
                ),
                "expected_id": int(expected_id),
                "expected_text": llm.detokenize([int(expected_id)], special=True).decode(
                    "utf-8", errors="replace"
                ),
                "expected_rank": _rank(logits, int(expected_id)),
                "eos_rank": _rank(logits, int(eos_id)),
                "eos_vs_expected_gap": float(logits[eos_id] - logits[expected_id]),
                "top": _top(llm, logits),
            }
        )
        if depth < len(output_ids):
            token_id = int(output_ids[depth])
            llm.eval([token_id])
            prefix.append(token_id)

    payload = {
        "attack_sha256": hashlib.sha256((ROOT / "attack.py").read_bytes()).hexdigest(),
        "model": args.model,
        "model_path": str(MODELS[args.model]),
        "renderer": "aicomp_sdk.agents.hf_chat_template.agent._render_hf_messages",
        "guardrail": "not_applicable_state_analysis",
        "candidate_count": len(candidates),
        "candidate_messages": list(candidates[0].user_messages),
        "candidate_sha256": hashlib.sha256(
            json.dumps(
                list(candidates[0].user_messages),
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()
        ).hexdigest(),
        "tool_call": {"name": call.tool_name, "arguments": call.arguments},
        "tool_result": "ok",
        "rendered_messages": rendered_messages,
        "prompt_tokens": len(prompt_ids),
        "prompt_tail": prompt[-1200:],
        "observed_output": output_text,
        "observed_output_ids": output_ids,
        "observed_output_tokens": len(output_ids),
        "eos_id": eos_id,
        "steps": steps,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "attack_sha256": payload["attack_sha256"],
                "model": args.model,
                "candidate_count": len(candidates),
                "prompt_tokens": len(prompt_ids),
                "observed_output_tokens": len(output_ids),
                "steps": steps,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
