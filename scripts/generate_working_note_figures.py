from __future__ import annotations

import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
JSON_DIR = ROOT / "sandbox" / "output"
OUT_DIR = ROOT / "report_assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)


ARTIFACTS = {
    "gpt_initial": "baseline_original200_gpt_optimal.json",
    "gpt_compact": "gpt_compact_http200_optimal.json",
    "gpt_no_final_1": "gpt_compact_no_final200_optimal.json",
    "gpt_no_final_2": "gpt_compact_no_final200_optimal_repeat.json",
    "gpt_duplicate_1": "gpt_duplicate_header_alignment200_optimal.json",
    "gpt_duplicate_2": "gpt_duplicate_header_alignment200_optimal_repeat.json",
    "gemma_initial": "baseline_original200_gemma_optimal.json",
    "gemma_bare": "gemma_bare_promoted200_optimal.json",
    "gemma_late_url_1": "gemma_zh_no_trailing_punctuation_24layers200_optimal.json",
    "gemma_late_url_2": "gemma_zh_no_trailing_punctuation_repeat_24layers200_optimal.json",
    "gpt_email_reorder_1": "gpt_email_emptyargs_numericto_tailreorder_99layers200_optimal_run1_20260830.json",
    "gpt_email_reorder_2": "gpt_email_emptyargs_numericto_tailreorder_99layers200_optimal_run2_20260830.json",
    "gpt_email_reorder_3": "gpt_email_emptyargs_numericto_tailreorder_99layers200_optimal_run3_20260830.json",
    "gemma_email_bare": "gemma_email_bareunderscore_shortto_24layers200_optimal_run1_20260830.json",
    "gpt_email_clean": "gpt_email_baseline_clean_99layers200_optimal_run1_20260831.json",
    "gemma_email_clean": "gemma_email_baseline_clean_24layers200_optimal_run1_20260831.json",
    "gpt_email_restored": "gpt_attackemail_modelspecific_restored_99layers200_optimal_run1_20260831.json",
    "gemma_email_restored_1": "gemma_attackemail_modelspecific_restored_24layers200_optimal_run1_20260831.json",
    "gemma_email_restored_2": "gemma_attackemail_modelspecific_restored_24layers200_optimal_run2_20260831.json",
}


def load_artifact(name: str) -> dict[str, Any]:
    path = JSON_DIR / ARTIFACTS[name]
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def average_metric(names: list[str], *keys: str) -> float:
    values: list[float] = []
    for name in names:
        value: Any = load_artifact(name)
        for key in keys:
            value = value[key]
        values.append(float(value))
    return mean(values)


def verify_functional_gate(names: list[str]) -> None:
    for name in names:
        artifact = load_artifact(name)
        assert artifact["validated_findings"] == 200, name
        assert artifact["unique_score_cells"] == 200, name
        assert artifact["official_failure"] is None, name


def draw_pipeline() -> None:
    labels = [
        "User\nmessage",
        "Chat template\n+ tokenizer",
        "First model\ngeneration",
        "Tool parser\n+ execution",
        "History\nreconstruction",
        "Post-tool\ngeneration",
    ]
    fig, ax = plt.subplots(figsize=(12.8, 2.8))
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 2.8)
    ax.axis("off")

    box_width = 1.65
    xs = [0.25, 2.35, 4.45, 6.55, 8.65, 10.75]
    fills = ["#DCEAF7", "#E7E2F3", "#DDEFE4", "#F7E7D4", "#E7E2F3", "#DDEFE4"]
    for index, (x, label, fill) in enumerate(zip(xs, labels, fills, strict=True)):
        box = FancyBboxPatch(
            (x, 0.85),
            box_width,
            1.1,
            boxstyle="round,pad=0.08,rounding_size=0.08",
            linewidth=1.2,
            edgecolor="#263238",
            facecolor=fill,
        )
        ax.add_patch(box)
        ax.text(x + box_width / 2, 1.4, label, ha="center", va="center", fontsize=10)
        if index < len(xs) - 1:
            arrow = FancyArrowPatch(
                (x + box_width + 0.08, 1.4),
                (xs[index + 1] - 0.08, 1.4),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.2,
                color="#263238",
            )
            ax.add_patch(arrow)

    ax.text(
        6.4,
        2.45,
        "The replay compiler: one user message becomes a two-generation program",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
    )
    ax.annotate(
        "The useful event already exists here",
        xy=(8.18, 0.82),
        xytext=(7.35, 0.22),
        ha="center",
        fontsize=9,
        arrowprops={"arrowstyle": "->", "color": "#555555"},
    )
    ax.annotate(
        "But replay still pays this call",
        xy=(11.58, 0.82),
        xytext=(11.15, 0.22),
        ha="center",
        fontsize=9,
        arrowprops={"arrowstyle": "->", "color": "#555555"},
    )
    fig.savefig(OUT_DIR / "replay_compiler_pipeline.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def draw_latency_decomposition() -> dict[str, Any]:
    groups = {
        "GPT-OSS\nHarmony program": ["gpt_duplicate_1", "gpt_duplicate_2"],
        "Gemma 4\nbare late-URL program": ["gemma_late_url_1", "gemma_late_url_2"],
    }
    rows: list[dict[str, float | str]] = []
    for label, names in groups.items():
        total = average_metric(names, "replay_elapsed_s")
        first = average_metric(names, "agent_turn_profile", "user_message", "latency_total_s")
        post = average_metric(names, "agent_turn_profile", "tool_result", "latency_total_s")
        rows.append(
            {
                "label": label,
                "first": first,
                "post": post,
                "other": max(0.0, total - first - post),
                "total": total,
            }
        )

    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    y = list(range(len(rows)))
    first_values = [float(row["first"]) for row in rows]
    post_values = [float(row["post"]) for row in rows]
    other_values = [float(row["other"]) for row in rows]
    ax.barh(y, first_values, color="#4C78A8", label="First generation")
    ax.barh(y, post_values, left=first_values, color="#F28E2B", label="Post-tool generation")
    left_other = [a + b for a, b in zip(first_values, post_values, strict=True)]
    ax.barh(y, other_values, left=left_other, color="#B8B8B8", label="Other runtime")
    ax.set_yticks(y, [str(row["label"]) for row in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Seconds for 200 candidates")
    ax.set_title("The second model generation is a first-class replay cost", fontweight="bold")
    ax.grid(axis="x", alpha=0.22)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper right")
    for index, row in enumerate(rows):
        ax.text(float(row["total"]) + 3.0, index, f'{float(row["total"]):.1f} s', va="center")
    ax.set_xlim(0, max(float(row["total"]) for row in rows) * 1.15)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "latency_decomposition.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {"rows": rows}


def draw_optimization_ladder() -> dict[str, Any]:
    gpt_steps = [
        ("Initial K1", average_metric(["gpt_initial"], "replay_elapsed_s")),
        ("Compact\nHarmony", average_metric(["gpt_compact"], "replay_elapsed_s")),
        ("No content\nafter tool", average_metric(["gpt_no_final_1", "gpt_no_final_2"], "replay_elapsed_s")),
        ("Parser-aligned\nheader", average_metric(["gpt_duplicate_1", "gpt_duplicate_2"], "replay_elapsed_s")),
    ]
    gemma_steps = [
        ("Initial K1", average_metric(["gemma_initial"], "replay_elapsed_s")),
        ("Bare argument\npolicy", average_metric(["gemma_bare"], "replay_elapsed_s")),
        ("Late URL +\nno punctuation", average_metric(["gemma_late_url_1", "gemma_late_url_2"], "replay_elapsed_s")),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.0))
    for ax, title, steps, color in [
        (axes[0], "GPT-OSS: optimize Harmony state", gpt_steps, "#4C78A8"),
        (axes[1], "Gemma 4: optimize output policy", gemma_steps, "#59A14F"),
    ]:
        x = list(range(len(steps)))
        values = [value for _, value in steps]
        ax.plot(x, values, color=color, marker="o", linewidth=2.4, markersize=7)
        ax.set_xticks(x, [label for label, _ in steps])
        ax.set_ylabel("Seconds for 200 candidates")
        ax.set_title(title, fontweight="bold")
        ax.grid(axis="y", alpha=0.22)
        ax.set_axisbelow(True)
        padding = (max(values) - min(values)) * 0.28 or 5.0
        ax.set_ylim(min(values) - padding, max(values) + padding)
        for idx, value in enumerate(values):
            ax.annotate(
                f"{value:.1f} s",
                (idx, value),
                textcoords="offset points",
                xytext=(0, 9),
                ha="center",
                fontsize=9,
            )
    fig.suptitle("One-variable changes produced two different optimization paths", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "optimization_ladder.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {"gpt_steps": gpt_steps, "gemma_steps": gemma_steps}


def write_manifest(latency: dict[str, Any], ladder: dict[str, Any]) -> None:
    artifact_manifest: dict[str, Any] = {}
    for key, filename in ARTIFACTS.items():
        path = JSON_DIR / filename
        artifact = load_artifact(key)
        artifact_manifest[key] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "attack_sha256": artifact.get("attack_sha256"),
            "model": artifact.get("model"),
            "replay_elapsed_s": artifact.get("replay_elapsed_s"),
            "validated_findings": artifact.get("validated_findings"),
            "unique_score_cells": artifact.get("unique_score_cells"),
            "official_failure": artifact.get("official_failure"),
        }
    bundle_paths = {
        "working_note": ROOT / "WORKING_NOTE_USER_MESSAGE_PROGRAM.md",
        "figure_generator": Path(__file__).resolve(),
        "replay_compiler_pipeline": OUT_DIR / "replay_compiler_pipeline.png",
        "latency_decomposition": OUT_DIR / "latency_decomposition.png",
        "optimization_ladder": OUT_DIR / "optimization_ladder.png",
    }
    bundle_manifest = {
        key: {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for key, path in bundle_paths.items()
    }
    payload = {
        "description": "Exact local sources and output bundle for the working note.",
        "artifacts": artifact_manifest,
        "bundle": bundle_manifest,
        "derived": {"latency_decomposition": latency, "optimization_ladder": ladder},
    }
    with (OUT_DIR / "figure_data_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    verify_functional_gate(list(ARTIFACTS))
    draw_pipeline()
    latency = draw_latency_decomposition()
    ladder = draw_optimization_ladder()
    write_manifest(latency, ladder)


if __name__ == "__main__":
    main()
