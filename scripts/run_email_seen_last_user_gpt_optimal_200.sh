#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/dreuxx/Downloads/openai"
PACKAGE_DIR="${PROJECT_DIR}/ai-agent-security-multi-step-tool-attacks"
ATTACK_SOURCE="/home/dreuxx/Downloads/attack(20260825-115958).py"
ATTACK_PATH="${PROJECT_DIR}/attack_email_seen_last_user_200.py"
GPT_MODEL="${PROJECT_DIR}/model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/gpt-oss-20b-Q4_K_M.gguf"

on_exit() {
    status=$?
    trap - EXIT
    if [[ ${status} -eq 0 ]]; then
        message="email.list -> email.send + last_user, GPT Optimal 200 terminó completo"
    else
        message="email.list -> email.send + last_user, GPT Optimal 200 terminó con error ${status}"
    fi
    printf '\n================================================================\n'
    printf 'ALERTA TERMINAL: %s\n' "${message}"
    printf '================================================================\n'
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "JED attack.py" "${message}" || true
    fi
    exit "${status}"
}
trap on_exit EXIT

cd "${PROJECT_DIR}"
cp -- "${ATTACK_SOURCE}" "${ATTACK_PATH}"
cmp --silent "${ATTACK_SOURCE}" "${ATTACK_PATH}"
printf 'TERMINAL ACTIVA: email.list -> email.send + last_user; GPT-OSS; Optimal; 200\n'
printf 'ATTACK_SOURCE: %s\n' "${ATTACK_SOURCE}"
printf 'ATTACK_RUNTIME_COPY: %s\n' "${ATTACK_PATH}"
printf 'ATTACK_SHA256: '
sha256sum "${ATTACK_PATH}"

PYTHONPYCACHEPREFIX=/tmp/email_seen_last_user_pycache \
    .venv/bin/python -m py_compile "${ATTACK_PATH}" validar_selector.py
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m aicomp_sdk.cli.main \
    validate redteam "${ATTACK_PATH}"
env SANDBOX_ALLOW_GPU=1 sandbox/run.sh .venv/bin/python -c \
    'from llama_cpp import llama_supports_gpu_offload; enabled=bool(llama_supports_gpu_offload()); print(f"gpu_offload={enabled}", flush=True); assert enabled'

printf '\n[%s] START email_seen_last_user200_gpt_optimal\n' "$(date -Is)"
env SANDBOX_ALLOW_GPU=1 sandbox/run.sh \
    .venv/bin/python validar_selector.py \
    gpt_oss "${GPT_MODEL}" \
    --attack-path "${ATTACK_PATH}" \
    --budget 8750 \
    --hard-cap 200 \
    --replay-limit 200 \
    --replay-budget 8750 \
    --n-gpu-layers -1 \
    --replay-guardrail optimal \
    --output sandbox/output/email_seen_last_user200_gpt_optimal.json
printf '[%s] END email_seen_last_user200_gpt_optimal\n' "$(date -Is)"
