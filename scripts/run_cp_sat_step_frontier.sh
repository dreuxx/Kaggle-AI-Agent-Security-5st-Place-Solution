#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/dreuxx/Downloads/openai"

on_exit() {
    status=$?
    trap - EXIT
    printf '\n===============================================================\n'
    printf 'ALERTA TERMINAL: CP-SAT frontera 1..8 termino con estado %s\n' "${status}"
    printf '===============================================================\n'
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "JED CP-SAT" "Frontera 1..8 termino con estado ${status}" || true
    fi
    exit "${status}"
}
trap on_exit EXIT

cd "${PROJECT_DIR}"
printf 'TERMINAL ACTIVA: CP-SAT modelo-libre; pasos 1..8\n'
.venv/bin/python -m py_compile cp_sat_multistep_bypass.py

for steps in 1 2 3 4 5 6 7 8; do
    printf '\n[%s] START max_steps=%s\n' "$(date -Is)" "${steps}"
    .venv/bin/python cp_sat_multistep_bypass.py \
        --max-steps "${steps}" \
        --top-k 3 \
        --solver-timeout-s 2 \
        --output-json "sandbox/output/cp_sat_frontier_s${steps}.json" \
        --output-csv "sandbox/output/cp_sat_frontier_s${steps}.csv"
    printf '[%s] END max_steps=%s\n' "$(date -Is)" "${steps}"
done
