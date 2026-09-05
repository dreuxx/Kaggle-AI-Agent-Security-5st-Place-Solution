#!/usr/bin/env python3
"""Read-only publication checks; never imports attack.py or starts a model."""
from __future__ import annotations
import ast
import hashlib
import json
import math
import re
import statistics
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check_file_manifest(root: Path = ROOT) -> int:
    rows = read_json(root / "provenance/file_manifest.json")["files"]
    for row in rows:
        path = root / row["path"]
        ensure(path.is_file(), f"Missing file: {row['path']}")
        ensure(path.stat().st_size == row["bytes"], f"Size changed: {row['path']}")
        ensure(digest(path) == row["sha256"], f"Checksum changed: {row['path']}")
    return len(rows)


def check_sources(root: Path = ROOT) -> int:
    rows = read_json(root / "provenance/source_manifest.json")["sources"]
    for row in rows:
        ensure(digest(root / row["path"]) == row["published_sha256"],
               f"Source changed: {row['path']}")
        if row["byte_identical"]:
            ensure(row["original_sha256"] == row["published_sha256"],
                   f"Inconsistent source identity: {row['path']}")
    for path in root.rglob("*.py"):
        ast.parse(path.read_bytes(), filename=str(path.relative_to(root)))
    ensure(digest(root / "attack.py") ==
           "2ababf986a963333118fbf19c282e7004057acc4191b3f5dd4db471c17ef2bf3",
           "Principal source differs from the snapshot cited by the Working Note")
    return len(rows)


def check_archived_records(root: Path = ROOT) -> int:
    rows = read_json(root / "experiments/artifact_manifest.json")["artifacts"]
    ensure(len(rows) == 24, "The documented selection has 24 artifacts")
    for row in rows:
        path = root / row["path"]
        ensure(digest(path) == row["published_sha256"], f"Artifact changed: {path.name}")
        data = read_json(path)
        if row["kind"] == "completed_replay":
            ensure(data["official_replay_complete"] is True, f"Incomplete record: {path.name}")
            ensure(data["validated_findings"] == 200 and data["unique_score_cells"] == 200,
                   f"Recorded gate differs: {path.name}")
            ensure(len(data["replays"]) == 200, f"Recorded row count differs: {path.name}")
            ensure(data.get("official_failure") is None, f"Recorded failure: {path.name}")
        else:
            ensure(isinstance(data.get("steps"), list) and bool(data["steps"]),
                   f"Missing diagnostic steps: {path.name}")
    return len(rows)


def check_arithmetic(root: Path = ROOT) -> int:
    rows = read_json(root / "experiments/artifact_manifest.json")["artifacts"]
    paths = {Path(row["path"]).name: root / row["path"] for row in rows}
    figures = read_json(root / "docs/Figure_Data.json")
    groups = {
        "GPT-OSS": ("gpt_duplicate_header_alignment200_optimal.json",
                    "gpt_duplicate_header_alignment200_optimal_repeat.json"),
        "Gemma": ("gemma_zh_no_trailing_punctuation_24layers200_optimal.json",
                  "gemma_zh_no_trailing_punctuation_repeat_24layers200_optimal.json"),
    }
    checks = 0
    for model, names in groups.items():
        records = [read_json(paths[name]) for name in names]
        measured = {
            "total_mean": statistics.mean(r["replay_elapsed_s"] for r in records),
            "first_mean": statistics.mean(r["agent_turn_profile"]["user_message"]["latency_total_s"] for r in records),
            "post_mean": statistics.mean(r["agent_turn_profile"]["tool_result"]["latency_total_s"] for r in records),
        }
        for metric, value in measured.items():
            ensure(math.isclose(value, figures["models"][model][metric], abs_tol=1e-5),
                   f"Figure mismatch: {model} {metric}")
            checks += 1
    probes = {
        "GPT-OSS": "gpt_posttool_stop_depth_20260828.json",
        "Gemma": "gemma_posttool_stop_depth_exact_renderer_20260828.json",
    }
    for model, name in probes.items():
        step = read_json(paths[name])["steps"][0]
        expected = figures["eog_diagnostics_reported"][model]
        ensure(step["eos_rank"] == expected["rank"], f"EOG rank differs: {model}")
        ensure(abs(step["eos_vs_expected_gap"] - expected["gap"]) < .01,
               f"EOG rounded gap differs: {model}")
        checks += 1
    times = [read_json(paths[
        f"gemma_email_compact_signature_noreply_28tok_graphs_24layers200_optimal_run{i}_20260831.json"
    ])["replay_elapsed_s"] for i in (1, 2, 3)]
    ensure(abs(statistics.mean(times) - 263.427367) < 1e-5, "Gemma email mean differs")
    return checks + 1


def check_doc_links(root: Path = ROOT) -> int:
    checked = 0
    for path in root.rglob("*.md"):
        for match in re.finditer(r"!?\[[^\]\n]*\]\(([^)\n]+)\)", path.read_text(encoding="utf-8")):
            target = match.group(1).strip().split(' "', 1)[0]
            if re.match(r"^[a-zA-Z][\w+.-]*:", target) or target.startswith("#"):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            ensure(resolved.is_relative_to(root.resolve()), f"Link leaves repository: {path.name}")
            ensure(resolved.exists(), f"Unresolved link in {path.relative_to(root)}: {target}")
            checked += 1
    return checked


def check_publication_patterns(root: Path = ROOT) -> int:
    # A bounded screen, not an exhaustive detector. No matched value is printed.
    patterns = {
        "Kaggle token": rb"KGAT_[A-Za-z0-9_-]{20,}",
        "GitHub token": rb"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})",
        "AWS-style key": rb"(?:AKIA|ASIA)[A-Z0-9]{16}",
        "private key": rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----",
        "common API token": rb"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}",
        "HF token": rb"hf_[A-Za-z0-9]{25,}",
    }
    checked = 0
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        data = path.read_bytes()
        for name, pattern in patterns.items():
            ensure(re.search(pattern, data) is None,
                   f"Review needed: {name} pattern in {path.relative_to(root)}")
        ensure(path.name != "kaggle.json" and not path.name.startswith(".env"),
               f"Credential/environment filename included: {path.relative_to(root)}")
        checked += 1
    return checked


def main() -> int:
    checks = (
        ("release checksums", check_file_manifest),
        ("source identity and syntax", check_sources),
        ("historical JSON records", check_archived_records),
        ("recorded numerical checks", check_arithmetic),
        ("local Markdown links", check_doc_links),
        ("bounded credential-pattern screen", check_publication_patterns),
    )
    try:
        for name, function in checks:
            print(f"PASS | {name}: {function()}")
    except (OSError, ValueError, KeyError, SyntaxError, TypeError) as exc:
        print(f"FAIL | {exc}", file=sys.stderr)
        return 1
    print("PUBLICATION_CHECKS_OK — static checks only; no model or private evaluation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
