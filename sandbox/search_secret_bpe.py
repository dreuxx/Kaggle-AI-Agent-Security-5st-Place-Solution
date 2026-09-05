from __future__ import annotations

import argparse
from collections import deque

from llama_cpp import Llama


MARKER = "SECRET_MARKER"


def decoded_piece(llm: Llama, token_id: int) -> str | None:
    try:
        raw = llm.detokenize([token_id], special=True)
        return raw.decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_path")
    args = parser.parse_args()

    llm = Llama(model_path=args.model_path, vocab_only=True, verbose=False)
    pieces = [decoded_piece(llm, token_id) for token_id in range(llm.n_vocab())]

    one = [(i, piece) for i, piece in enumerate(pieces) if piece and MARKER in piece]
    two: list[tuple[int, str, int, str, str]] = []

    # A two-token string containing MARKER must split MARKER at one of its
    # internal boundaries. Extra prefix/suffix text is allowed because the
    # scorer only requires substring containment.
    for split in range(1, len(MARKER)):
        left = MARKER[:split]
        right = MARKER[split:]
        left_ids = [
            (i, piece)
            for i, piece in enumerate(pieces)
            if piece is not None and piece.endswith(left)
        ]
        right_ids = [
            (i, piece)
            for i, piece in enumerate(pieces)
            if piece is not None and piece.startswith(right)
        ]
        for left_id, left_piece in left_ids:
            for right_id, right_piece in right_ids:
                joined = left_piece + right_piece
                if MARKER not in joined:
                    continue
                encoded = llm.tokenize(joined.encode("utf-8"), add_bos=False, special=True)
                if len(encoded) == 2:
                    two.append((left_id, left_piece, right_id, right_piece, joined))

    baseline = llm.tokenize(MARKER.encode("utf-8"), add_bos=False, special=True)

    # Find the shortest vocabulary-piece path whose concatenated decoded text
    # contains MARKER. The first and last pieces may carry arbitrary exterior
    # text; interior pieces must match the marker exactly so containment is
    # preserved.
    marker_len = len(MARKER)
    edges: dict[int, list[tuple[int, int, str]]] = {
        pos: [] for pos in range(marker_len + 1)
    }
    for token_id, piece in enumerate(pieces):
        if not piece:
            continue
        if MARKER in piece:
            edges[0].append((marker_len, token_id, piece))
        for end in range(1, marker_len + 1):
            if piece.endswith(MARKER[:end]):
                edges[0].append((end, token_id, piece))
        for start in range(1, marker_len):
            remainder = MARKER[start:]
            if piece.startswith(remainder):
                edges[start].append((marker_len, token_id, piece))
            for end in range(start + 1, marker_len):
                if piece == MARKER[start:end]:
                    edges[start].append((end, token_id, piece))

    queue = deque([(0, [])])
    best_depth: dict[int, int] = {0: 0}
    shortest: list[tuple[int, str]] | None = None
    while queue:
        position, path = queue.popleft()
        if position == marker_len:
            shortest = path
            break
        for next_position, token_id, piece in edges[position]:
            depth = len(path) + 1
            if depth >= best_depth.get(next_position, 1_000_000):
                continue
            best_depth[next_position] = depth
            queue.append((next_position, [*path, (token_id, piece)]))

    shortest_joined = "" if shortest is None else "".join(piece for _, piece in shortest)
    shortest_retokenized = (
        []
        if shortest is None
        else llm.tokenize(shortest_joined.encode("utf-8"), add_bos=False, special=True)
    )
    print({
        "n_vocab": llm.n_vocab(),
        "baseline_ids": baseline,
        "baseline_n": len(baseline),
        "one_token_matches": one[:20],
        "two_token_match_count": len(two),
        "two_token_examples": two[:50],
        "shortest_piece_path": shortest,
        "shortest_joined": shortest_joined,
        "shortest_retokenized": shortest_retokenized,
    })


if __name__ == "__main__":
    main()
