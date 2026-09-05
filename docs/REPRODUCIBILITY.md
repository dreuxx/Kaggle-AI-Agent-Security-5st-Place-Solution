# Reproducibility and verification

## Three different questions

**Publication integrity:** do the supplied files match the release manifest, and do the archived values support the report? This can be checked with the standard-library verifier.

**Historical experiment reproduction:** can the matching model, embedded template, source version, SDK, and settings produce comparable behavior? That requires the historical runtime and source state, not merely the current `attack.py`.

**Private leaderboard reproduction:** can the held-out Kaggle defense reproduce the score? That cannot be established from the public source and local records supplied here.

## What the local check does

Run `python scripts/verify_release.py` from the repository root. It reads files only. It checks hashes, Python syntax, complete-replay flags and recorded counts for selected full replays, EOG records, the figure’s central means, and relative links in publication documents.

Run `python -m unittest discover -s tests -v` for the corresponding release-integrity tests. No external Python dependency is needed. Neither command imports the attack module, starts a model, uses network credentials, or invokes a tool-using agent.

## Historical environment recorded by the note

| Component | Recorded configuration |
|---|---|
| Models | Competition GPT-OSS 20B and Gemma 4 26B-A4B-it GGUFs |
| Backend | `llama-cpp-python` 0.3.34 |
| Decoding | Deterministic; operational context 8,192 |
| Local hardware | RTX A5000 |
| Gemma finalist timings | 24 GPU-offloaded layers |
| Separate language ablation | 23 GPU-offloaded layers |
| Mature comparison size | 200 actual candidates |
| Candidate/tool loop | Competition parser and evaluator, up to eight hops |

This is a record of the experiment setup, not an installation lockfile validated in this publication environment. The uploaded ZIP does not provide a verified standalone SDK distribution, all matching source states, or model weights. No replacement wheel or fabricated dependency lock has been added.

## Source and data boundaries

The root source is the separately supplied email implementation cited by the polished note. It is unchanged. The ZIP’s HTTP and 200-candidate variants are preserved under `research/variants`. The exact v57 kernel remains unauthenticated according to the supplied final audit.

Archived replays include their own source and template identities. Privacy redaction changes file bytes, so both original and published hashes are recorded. It does not turn a historical result into a new replay. The selected full-replay rows and candidate text have been checked for equality before and after sanitization.

Do not substitute a 24-layer timing for the 23-layer comparison, a local surrogate result for a held-out result, or the current file hash for every historical experiment.
