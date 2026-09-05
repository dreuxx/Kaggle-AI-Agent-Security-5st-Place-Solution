#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/dreuxx/Downloads/openai"
PACKAGE_DIR="${PROJECT_DIR}/ai-agent-security-multi-step-tool-attacks"
GEMMA_MODEL="${PROJECT_DIR}/model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
EXPECTED_SHA="2a0de79fd8b7f2508fb7aae7a6d9f99a4ce68bbbb240551c34df163a71aafa51"

on_exit() {
    status=$?
    trap - EXIT
    printf '\n================================================================\n'
    printf 'ALERTA TERMINAL: Gemma baseline post-bare 200 termino con estado %s\n' "${status}"
    printf '================================================================\n'
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "JED replay" "Gemma baseline post-bare 200 termino con estado ${status}" || true
    fi
    exit "${status}"
}
trap on_exit EXIT

cd "${PROJECT_DIR}"
printf 'TERMINAL ACTIVA: Gemma baseline post-bare; Optimal; 200\n'
actual_sha=$(sha256sum attack.py | cut -d' ' -f1)
printf 'ATTACK_SHA256=%s\n' "${actual_sha}"
test "${actual_sha}" = "${EXPECTED_SHA}"

.venv/bin/python -m py_compile attack.py validar_selector.py tests/test_attack_frontier.py
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m unittest \
    tests.test_attack_frontier.AttackFrontierTests.test_fixed_gemma_portfolio_is_unique_and_does_not_touch_env \
    tests.test_attack_frontier.AttackFrontierTests.test_full_fixed_gemma_portfolio_is_uniform_and_adaptive
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m aicomp_sdk.cli.main validate redteam attack.py
env SANDBOX_ALLOW_GPU=1 sandbox/run.sh .venv/bin/python -c \
    'from llama_cpp import llama_supports_gpu_offload; enabled=bool(llama_supports_gpu_offload()); print(f"gpu_offload={enabled}", flush=True); assert enabled'

env SANDBOX_ALLOW_GPU=1 sandbox/run.sh \
    .venv/bin/python validar_selector.py \
    gemma "${GEMMA_MODEL}" \
    --budget 8750 \
    --hard-cap 200 \
    --replay-limit 200 \
    --replay-budget 8750 \
    --n-gpu-layers 24 \
    --replay-guardrail optimal \
    --output sandbox/output/gemma_bare_chatinject200_gemma_baseline_after.json
