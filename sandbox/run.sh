#!/usr/bin/env bash
set -euo pipefail

SANDBOX_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd -- "${SANDBOX_DIR}/.." && pwd -P)"
PACKAGE_DIR="${PROJECT_ROOT}/ai-agent-security-multi-step-tool-attacks"
OUTPUT_DIR="${SANDBOX_DIR}/output"
OFFLINE_HOOK_DIR="${SANDBOX_DIR}/offline"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"

usage() {
    cat <<'EOF'
Uso:
  sandbox/run.sh COMANDO [ARGUMENTOS...]

Ejemplo:
  sandbox/run.sh .venv/bin/python sandbox/self_test.py
EOF
}

if [[ $# -eq 0 ]]; then
    usage
    exit 2
fi

if ! command -v bwrap >/dev/null 2>&1; then
    echo "Error: bubblewrap (bwrap) no esta instalado." >&2
    exit 1
fi

if [[ ! -x "${VENV_PYTHON}" ]]; then
    echo "Error: no existe el Python local esperado: ${VENV_PYTHON}" >&2
    exit 1
fi

mkdir -p -- "${OUTPUT_DIR}"

USER_SITE="$(${VENV_PYTHON} -c 'import site; print(site.getusersitepackages())')"
if [[ ! -d "${USER_SITE}" ]]; then
    echo "Error: no existe el directorio local de dependencias: ${USER_SITE}" >&2
    exit 1
fi

CUDA_LIB_DIR="/usr/local/lib/ollama/cuda_v12"
if [[ ! -d "${CUDA_LIB_DIR}" ]]; then
    echo "Error: falta el runtime CUDA local requerido: ${CUDA_LIB_DIR}" >&2
    exit 1
fi

PRIVATE_GUARDRAIL_WHEEL="/home/dreuxx/Documents/arc/val/aicomp_private_guardrails-4.0.0-py3-none-any.whl"
SANDBOX_PRIVATE_GUARDRAIL_WHEEL="/aicomp_private_guardrails-4.0.0-py3-none-any.whl"
if [[ ! -f "${PRIVATE_GUARDRAIL_WHEEL}" ]]; then
    echo "Error: falta el wheel privado local: ${PRIVATE_GUARDRAIL_WHEEL}" >&2
    exit 1
fi

DEVICE_ARGS=(--dev /dev)
if [[ "${SANDBOX_ALLOW_GPU:-0}" == "1" ]]; then
    DEVICE_ARGS=(--dev-bind /dev /dev)
fi

exec bwrap \
    --die-with-parent \
    --new-session \
    --unshare-pid \
    --unshare-uts \
    --unshare-ipc \
    --hostname openai-isolated \
    --cap-drop ALL \
    --ro-bind /usr /usr \
    --ro-bind /bin /bin \
    --ro-bind /lib /lib \
    --ro-bind /lib64 /lib64 \
    --ro-bind /etc /etc \
    --ro-bind "${USER_SITE}" "${USER_SITE}" \
    --ro-bind "${PRIVATE_GUARDRAIL_WHEEL}" "${SANDBOX_PRIVATE_GUARDRAIL_WHEEL}" \
    --ro-bind "${PROJECT_ROOT}" "${PROJECT_ROOT}" \
    --bind "${OUTPUT_DIR}" "${OUTPUT_DIR}" \
    --proc /proc \
    "${DEVICE_ARGS[@]}" \
    --tmpfs /tmp \
    --dir /tmp/home \
    --chdir "${PROJECT_ROOT}" \
    --clearenv \
    --setenv HOME /tmp/home \
    --setenv USER sandbox \
    --setenv LOGNAME sandbox \
    --setenv LANG C.UTF-8 \
    --setenv LC_ALL C.UTF-8 \
    --setenv PATH "${PROJECT_ROOT}/.venv/bin:/usr/bin:/bin" \
    --setenv PYTHONPATH "${OFFLINE_HOOK_DIR}:${PACKAGE_DIR}:${USER_SITE}:${SANDBOX_PRIVATE_GUARDRAIL_WHEEL}" \
    --setenv LD_LIBRARY_PATH "${CUDA_LIB_DIR}" \
    --setenv PYTHONDONTWRITEBYTECODE 1 \
    --setenv PYTHONNOUSERSITE 1 \
    --setenv HF_HUB_OFFLINE 1 \
    --setenv TRANSFORMERS_OFFLINE 1 \
    --setenv HF_DATASETS_OFFLINE 1 \
    --setenv HTTP_PROXY http://127.0.0.1:9 \
    --setenv HTTPS_PROXY http://127.0.0.1:9 \
    --setenv ALL_PROXY socks5://127.0.0.1:9 \
    --setenv NO_PROXY "" \
    --setenv SANDBOX_ACTIVE 1 \
    --setenv SANDBOX_OUTPUT "${OUTPUT_DIR}" \
    --setenv SANDBOX_NETWORK_MODE host-restricted+python-deny \
    "$@"
