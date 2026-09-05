#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/dreuxx/Downloads/openai"
PACKAGE_DIR="${PROJECT_DIR}/ai-agent-security-multi-step-tool-attacks"
GPT_MODEL="${PROJECT_DIR}/model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/gpt-oss-20b-Q4_K_M.gguf"
GEMMA_MODEL="${PROJECT_DIR}/model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
RUN_LABEL_PREFIX="${1:-optimal200}"

on_exit() {
    status=$?
    trap - EXIT
    printf '\n[%s] Optimal 200 termino con estado %s\n' "$(date -Is)" "${status}"
    exit "${status}"
}
trap on_exit EXIT

cd "${PROJECT_DIR}"

printf '[1/5] Compilacion y validador oficial\n'
.venv/bin/python -m py_compile attack.py validar_selector.py
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m aicomp_sdk.cli.main validate redteam attack.py

printf '[2/5] Invariantes: exactamente 200 por modelo\n'
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python - <<'PY'
import attack
from aicomp_sdk.attacks.contracts import AttackRunConfig

for model in ("gpt_oss", "gemma"):
    candidates = attack.AttackAlgorithm(config={"fixed_model": model}).run(
        None,
        AttackRunConfig(time_budget_s=8750, max_tool_hops=8),
    )
    assert len(candidates) == 200
    assert len({tuple(candidate.user_messages) for candidate in candidates}) == 200
    assert all(len(candidate.user_messages) == 1 for candidate in candidates)
    print(model, "candidates=200 unique=200 messages=1")
PY

printf '[3/5] GPU visible dentro del sandbox\n'
env SANDBOX_ALLOW_GPU=1 sandbox/run.sh .venv/bin/python -c \
    'from llama_cpp import llama_supports_gpu_offload; print("gpu_offload=", llama_supports_gpu_offload())'

run_case() {
    model=$1
    model_path=$2
    gpu_layers=$3
    label=$4
    printf '\n[%s] START %s\n' "$(date -Is)" "${label}"
    env SANDBOX_ALLOW_GPU=1 sandbox/run.sh \
        .venv/bin/python validar_selector.py \
        "${model}" "${model_path}" \
        --budget 8750 \
        --hard-cap 200 \
        --replay-limit 200 \
        --replay-budget 8750 \
        --n-gpu-layers "${gpu_layers}" \
        --replay-guardrail optimal \
        --output "sandbox/output/${label}.json"
    printf '[%s] END %s\n' "$(date -Is)" "${label}"
}

printf '[4/5] GPT-OSS / Optimal\n'
run_case gpt_oss "${GPT_MODEL}" -1 "${RUN_LABEL_PREFIX}_gpt_optimal"

printf '[5/5] Gemma / Optimal\n'
run_case gemma "${GEMMA_MODEL}" 24 "${RUN_LABEL_PREFIX}_gemma_optimal"
