#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/dreuxx/Downloads/openai"
PACKAGE_DIR="${PROJECT_DIR}/ai-agent-security-multi-step-tool-attacks"
GEMMA_MODEL="${PROJECT_DIR}/model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"

on_exit() {
    status=$?
    trap - EXIT
    printf '\n[%s] Gemma unconditional A/B termino con estado %s\n' "$(date -Is)" "${status}"
    exit "${status}"
}
trap on_exit EXIT

cd "${PROJECT_DIR}"

printf '[1/5] Python compile\n'
.venv/bin/python -m py_compile attack.py tests/test_attack_frontier.py

printf '[2/5] Unit tests\n'
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m unittest tests.test_attack_frontier

printf '[3/5] Official validator\n'
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m aicomp_sdk.cli.main validate redteam attack.py

run_case() {
    label=$1
    guardrail=$2
    printf '\n[%s] START %s\n' "$(date -Is)" "${label}"
    env SANDBOX_ALLOW_GPU=1 sandbox/run.sh \
        .venv/bin/python validar_selector.py \
        gemma "${GEMMA_MODEL}" \
        --fixed-experiment-arm gemma_hybrid_k3_lss3 \
        --hard-cap 3 \
        --replay-limit 3 \
        --replay-budget 900 \
        --n-gpu-layers 24 \
        --replay-guardrail "${guardrail}" \
        --output "sandbox/output/${label}.json"
    printf '[%s] END %s\n' "$(date -Is)" "${label}"
}

printf '[4/5] Gemma unconditional / Optimal\n'
run_case gemma_hybrid_k3_lss3_s3_optimal optimal

printf '[5/5] Gemma unconditional / strict\n'
run_case gemma_hybrid_k3_lss3_s3_strict strict
