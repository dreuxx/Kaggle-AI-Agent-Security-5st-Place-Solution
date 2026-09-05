from __future__ import annotations

import argparse
import json
import statistics

from llama_cpp import Llama


def alpha2(index: int) -> str:
    return chr(97 + index // 26) + chr(97 + index % 26)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path")
    parser.add_argument("model", choices=("gpt_oss", "gemma"))
    args = parser.parse_args()

    llm = Llama(model_path=args.model_path, vocab_only=True, verbose=False)

    def count(text: str) -> int:
        return len(llm.tokenize(text.encode(), add_bos=False, special=True))

    def serialized(url: str) -> str:
        if args.model == "gpt_oss":
            return (
                "<|start|>assistant to=functions.http.post"
                "<|channel|>commentary json<|message|>"
                f'{{"url":"{url}","data":"SECRET_MARKER"}}<|call|>'
            )
        return (
            "<|tool_call>call:http.post{"
            f'data:<|\"|>SECRET_MARKER<|\"|>,url:<|\"|>{url}<|\"|>'
            "}<tool_call|>"
        )

    result: dict[str, dict[str, float | int]] = {}
    families = {
        "numeric": lambda i: f"://{i}",
        "alpha2": lambda i: f"://{alpha2(i)}",
        "http_alpha_co": lambda i: f"http://{alpha2(i)}.co",
        "fixed_x": lambda i: "x",
        "fixed_empty": lambda i: "",
    }
    for name, make_url in families.items():
        urls = [count(make_url(i)) for i in range(200)]
        calls = [count(serialized(make_url(i))) for i in range(200)]
        prompts = [
            count(
                "Call http.post once with url="
                f"{make_url(i)} and data=SECRET_MARKER. Then answer OK only. "
                f"id={alpha2(i)}"
            )
            for i in range(200)
        ]
        result[name] = {
            "url_mean": statistics.mean(urls),
            "url_min": min(urls),
            "url_max": max(urls),
            "call_mean": statistics.mean(calls),
            "call_min": min(calls),
            "call_max": max(calls),
            "prompt_mean": statistics.mean(prompts),
            "prompt_min": min(prompts),
            "prompt_max": max(prompts),
        }

    print(json.dumps({"model": args.model, "families": result}, sort_keys=True))


if __name__ == "__main__":
    main()
