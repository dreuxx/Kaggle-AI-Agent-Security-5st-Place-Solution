#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/dreuxx/Downloads/openai"
PACKAGE_DIR="${PROJECT_DIR}/ai-agent-security-multi-step-tool-attacks"
GPT_MODEL="${PROJECT_DIR}/model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/gpt-oss-20b-Q4_K_M.gguf"
GEMMA_MODEL="${PROJECT_DIR}/model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
EXPECTED_SHA="16da28cf5ab2e9dcdc0024e16431775baff469d04fb257e4d0fdb1930677826b"

on_exit() {
    status=$?
    trap - EXIT
    printf '\n================================================================\n'
    printf 'ALERTA TERMINAL: Fast answers, Optimal 200 termino con estado %s\n' "${status}"
    printf '================================================================\n'
    exit "${status}"
}
trap on_exit EXIT

cd "${PROJECT_DIR}"
printf 'TERMINAL ACTIVA: Fast answers, Optimal, 200, GPT y Gemma\n'
actual_sha=$(sha256sum attack.py | cut -d' ' -f1)
printf 'ATTACK_SHA256=%s\n' "${actual_sha}"
test "${actual_sha}" = "${EXPECTED_SHA}"

.venv/bin/python -m py_compile attack.py validar_selector.py
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m aicomp_sdk.cli.main validate redteam attack.py
env SANDBOX_ALLOW_GPU=1 sandbox/run.sh .venv/bin/python -c \
    'from llama_cpp import llama_supports_gpu_offload; enabled=bool(llama_supports_gpu_offload()); print(f"gpu_offload={enabled}", flush=True); assert enabled'

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

run_case gpt_oss "${GPT_MODEL}" -1 fast_answers200_gpt_optimal
run_case gemma "${GEMMA_MODEL}" 24 fast_answers200_gemma_optimal
