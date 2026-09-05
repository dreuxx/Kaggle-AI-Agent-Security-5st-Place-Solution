#!/usr/bin/env bash
set -euo pipefail

project_dir="/home/dreuxx/Downloads/openai"
python_bin=".venv/bin/python"
attack_path="experiments/attack_priv02_retro_cd3_200.py"
gpt_model="model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/gpt-oss-20b-Q4_K_M.gguf"
gemma_model="model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
output_dir="sandbox/output"

cd "$project_dir"

finish_alert() {
    status=$?
    if [ "$status" -eq 0 ]; then
        message="PRIV-02 200 terminó: GPT-OSS y Gemma completos"
    else
        message="PRIV-02 200 terminó con error (status $status)"
    fi
    echo
    echo "================================================================"
    echo "ALERTA TERMINAL: $message"
    echo "================================================================"
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "Codex - experimento terminado" "$message" >/dev/null 2>&1 || true
    fi
    exit "$status"
}
trap finish_alert EXIT

echo "TERMINAL ACTIVA: PRIV-02, 200 candidatos exactos por modelo"
echo "Fase 0/2: comprobación estática y GPU"
"$python_bin" -m py_compile validar_selector.py "$attack_path"
"$python_bin" - <<'PY'
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path("ai-agent-security-multi-step-tool-attacks").resolve()))
path = Path("experiments/attack_priv02_retro_cd3_200.py").resolve()
spec = importlib.util.spec_from_file_location("priv02_preflight", path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)
algorithm = module.AttackAlgorithm(config={})
candidates = algorithm.run(None, None)
assert len(candidates) == 200
assert len({candidate.user_messages for candidate in candidates}) == 200
assert all(len(candidate.user_messages) == 2 for candidate in candidates)
print("preflight_portfolio=OK candidates=200 unique=200 messages=2")
PY

SANDBOX_ALLOW_GPU=1 sandbox/run.sh "$python_bin" - <<'PY'
from llama_cpp import llama_supports_gpu_offload

enabled = bool(llama_supports_gpu_offload())
print(f"gpu_offload={enabled}", flush=True)
if not enabled:
    raise SystemExit("GPU offload no está disponible; no se iniciará una prueba CPU lenta")
PY

echo "Fase 1/2: GPT-OSS OptimalGuardrail, replay 200/200"
SANDBOX_ALLOW_GPU=1 sandbox/run.sh "$python_bin" validar_selector.py \
    gpt_oss "$gpt_model" \
    --attack-path "$attack_path" \
    --budget 8750 \
    --replay-limit 200 \
    --replay-budget 8750 \
    --hard-cap 200 \
    --n-gpu-layers -1 \
    --replay-guardrail optimal \
    --output "$output_dir/priv02_retro_cd3_200_gpt_optimal.json"

echo "Fase 2/2: Gemma OptimalGuardrail, replay 200/200"
SANDBOX_ALLOW_GPU=1 sandbox/run.sh "$python_bin" validar_selector.py \
    gemma "$gemma_model" \
    --attack-path "$attack_path" \
    --budget 8750 \
    --replay-limit 200 \
    --replay-budget 8750 \
    --hard-cap 200 \
    --n-gpu-layers 24 \
    --replay-guardrail optimal \
    --output "$output_dir/priv02_retro_cd3_200_gemma_optimal.json"
