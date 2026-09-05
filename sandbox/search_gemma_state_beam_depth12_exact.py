#!/usr/bin/env python3
"""Continue the exact attack.py-backed Gemma post-tool beam from depth 8 to 12."""

from __future__ import annotations

from pathlib import Path

import search_gemma_state_beam_deep_exact as search


ROOT = Path(__file__).resolve().parents[1]
search.SOURCE = ROOT / "sandbox/output/gemma_state_beam_deep_exact_20260828.json"
search.OUTPUT = ROOT / "sandbox/output/gemma_state_beam_depth12_exact_20260828.json"
search.START_DEPTH = 8
search.MAX_DEPTH = 12
search.BEAM_WIDTH = 12
search.FINALIST_COUNT = 48


if __name__ == "__main__":
    search.main()
