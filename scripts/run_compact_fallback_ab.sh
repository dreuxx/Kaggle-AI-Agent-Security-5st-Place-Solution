#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/dreuxx/Downloads/openai"
PACKAGE_DIR="${PROJECT_DIR}/ai-agent-security-multi-step-tool-attacks"
GPT_MODEL="${PROJECT_DIR}/model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/gpt-oss-20b-Q4_K_M.gguf"
GEMMA_MODEL="${PROJECT_DIR}/model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"

on_exit() {
    status=$?
    trap - EXIT
    if [[ ${status} -eq 0 ]]; then
        message="Compact fallback A/B terminado correctamente"
    else
        message="Compact fallback A/B termino con error ${status}"
    fi
    printf '\n[%s] %s\n' "$(date -Is)" "${message}"
    exit "${status}"
}
trap on_exit EXIT

cd "${PROJECT_DIR}"

printf '[1/7] Python compile\n'
.venv/bin/python -m py_compile attack.py tests/test_attack_frontier.py

printf '[2/7] Unit tests\n'
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m unittest tests.test_attack_frontier

printf '[3/7] Official validator\n'
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m aicomp_sdk.cli.main validate redteam attack.py

run_case() {
    label=$1
    model=$2
    model_path=$3
    arm=$4
    guardrail=$5
    samples=$6
    gpu_layers=$7

    printf '\n[%s] START %s\n' "$(date -Is)" "${label}"
    env SANDBOX_ALLOW_GPU=1 sandbox/run.sh \
        .venv/bin/python validar_selector.py \
        "${model}" "${model_path}" \
        --fixed-experiment-arm "${arm}" \
        --hard-cap "${samples}" \
        --replay-limit "${samples}" \
        --replay-budget 900 \
        --n-gpu-layers "${gpu_layers}" \
        --replay-guardrail "${guardrail}" \
        --output "sandbox/output/${label}.json"
    printf '[%s] END %s\n' "$(date -Is)" "${label}"
}

printf '[4/7] GPT compact / Optimal\n'
run_case gpt_adaptive_k3_lss3_s5_optimal gpt_oss "${GPT_MODEL}" gpt_adaptive_k3_lss3 optimal 5 -1

printf '[5/7] GPT compact / strict\n'
run_case gpt_adaptive_k3_lss3_s5_strict gpt_oss "${GPT_MODEL}" gpt_adaptive_k3_lss3 strict 5 -1

printf '[6/7] Gemma compact / Optimal\n'
run_case gemma_adaptive_k3_lss3_s3_optimal gemma "${GEMMA_MODEL}" gemma_adaptive_k3_lss3 optimal 3 24

printf '[7/7] Gemma compact / strict\n'
run_case gemma_adaptive_k3_lss3_s3_strict gemma "${GEMMA_MODEL}" gemma_adaptive_k3_lss3 strict 3 24
