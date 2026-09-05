#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/dreuxx/Downloads/openai"
PACKAGE_DIR="${PROJECT_DIR}/ai-agent-security-multi-step-tool-attacks"

on_exit() {
    status=$?
    trap - EXIT
    printf '\n[%s] Validacion attack.py termino con estado %s\n' "$(date -Is)" "${status}"
    exit "${status}"
}
trap on_exit EXIT

cd "${PROJECT_DIR}"
printf '[1/3] Python compile\n'
.venv/bin/python -m py_compile attack.py tests/test_attack_frontier.py
printf '[2/3] Unit tests\n'
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m unittest tests.test_attack_frontier
printf '[3/3] Official validator\n'
env PYTHONPATH="${PACKAGE_DIR}" .venv/bin/python -m aicomp_sdk.cli.main validate redteam attack.py
