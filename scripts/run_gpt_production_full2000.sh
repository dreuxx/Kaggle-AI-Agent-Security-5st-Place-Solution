#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/dreuxx/Downloads/openai"
PACKAGE_DIR="${PROJECT_DIR}/ai-agent-security-multi-step-tool-attacks"
GPT_MODEL="${PROJECT_DIR}/model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/gpt-oss-20b-Q4_K_M.gguf"

on_exit() {
    status=$?
    trap - EXIT
    printf '\n[%s] GPT production full2000 termino con estado %s\n' "$(date -Is)" "${status}"
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
        gpt_oss "${GPT_MODEL}" \
        --budget 8750 \
        --hard-cap 2000 \
        --replay-limit 2000 \
        --replay-budget 8750 \
        --n-gpu-layers -1 \
        --replay-guardrail "${guardrail}" \
        --output "sandbox/output/${label}.json"
    printf '[%s] END %s\n' "$(date -Is)" "${label}"
}

printf '[4/5] GPT production full2000 / Optimal\n'
run_case gpt_production_full2000_optimal optimal

printf '[5/5] GPT production full2000 / strict surrogate\n'
run_case gpt_production_full2000_strict strict
