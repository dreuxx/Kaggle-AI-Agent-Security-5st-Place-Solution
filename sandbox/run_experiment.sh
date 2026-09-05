#!/usr/bin/env bash
set -euo pipefail

SANDBOX_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd -- "${SANDBOX_DIR}/.." && pwd -P)"

if [[ $# -lt 2 ]]; then
    cat >&2 <<'EOF'
Uso:
  sandbox/run_experiment.sh MODELO ARCHIVO_SALIDA [OPCIONES]

MODELO: gpt_oss o gemma
ARCHIVO_SALIDA: nombre JSON, sin directorios

Ejemplo:
  sandbox/run_experiment.sh gemma gemma_smoke.json --samples 1 --variants baseline_k1
EOF
    exit 2
fi

MODEL="$1"
OUTPUT_NAME="$2"
shift 2

if [[ "${OUTPUT_NAME}" == */* || "${OUTPUT_NAME}" != *.json ]]; then
    echo "Error: ARCHIVO_SALIDA debe ser un nombre .json sin directorios." >&2
    exit 2
fi

for argument in "$@"; do
    if [[ "${argument}" == "--output" || "${argument}" == --output=* ]]; then
        echo "Error: --output lo controla el sandbox." >&2
        exit 2
    fi
done

case "${MODEL}" in
    gpt_oss)
        MODEL_PATH="${PROJECT_ROOT}/model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/gpt-oss-20b-Q4_K_M.gguf"
        ;;
    gemma)
        MODEL_PATH="${PROJECT_ROOT}/model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
        ;;
    *)
        echo "Error: MODELO debe ser gpt_oss o gemma." >&2
        exit 2
        ;;
esac

exec bash "${SANDBOX_DIR}/run.sh" \
    .venv/bin/python \
    experimentos_modelos.py \
    "${MODEL}" \
    "${MODEL_PATH}" \
    "$@" \
    --output "${SANDBOX_DIR}/output/${OUTPUT_NAME}"
