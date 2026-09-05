#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/dreuxx/Downloads/openai"
GPT_MODEL="${PROJECT_DIR}/model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/gpt-oss-20b-Q4_K_M.gguf"
GEMMA_MODEL="${PROJECT_DIR}/model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"

on_exit() {
    status=$?
    trap - EXIT
    printf '\n================================================================\n'
    printf 'ALERTA TERMINAL: min-url+nonce Optimal 200 termino con estado %s\n' "${status}"
    printf '================================================================\n'
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "JED replay" "min-url+nonce Optimal 200 termino con estado ${status}" || true
    fi
    exit "${status}"
}
trap on_exit EXIT

cd "${PROJECT_DIR}"
printf 'TERMINAL ACTIVA: min-url+nonce; Optimal; 200; GPT seguido por Gemma\n'
printf 'ATTACK_SHA256: '
sha256sum attack.py

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

run_case gpt_oss "${GPT_MODEL}" -1 min_url_nonce200_gpt_optimal
run_case gemma "${GEMMA_MODEL}" 24 min_url_nonce200_gemma_optimal
