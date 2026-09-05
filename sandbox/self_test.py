#!/usr/bin/env python3
"""Verify the observable isolation guarantees of sandbox/run.sh."""

from __future__ import annotations

import json
import os
import socket
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.environ.get("SANDBOX_OUTPUT", ""))


def main() -> int:
    checks: dict[str, bool] = {}
    details: dict[str, str] = {}

    checks["sandbox_active"] = os.environ.get("SANDBOX_ACTIVE") == "1"
    checks["attack_readable"] = (PROJECT_ROOT / "attack.py").is_file()
    checks["attack_not_writable"] = not os.access(PROJECT_ROOT / "attack.py", os.W_OK)
    project_probe = PROJECT_ROOT / ".sandbox-write-probe"
    try:
        project_probe.write_text("should fail\n", encoding="utf-8")
    except OSError as error:
        checks["project_write_denied"] = True
        details["project_write_error"] = str(error)
    else:  # pragma: no cover - isolation failure path
        checks["project_write_denied"] = False
        details["project_write_error"] = "El montaje del proyecto acepto una escritura"
        project_probe.unlink(missing_ok=True)
    checks["gpt_oss_present"] = (
        PROJECT_ROOT
        / "model/gpt-oss-20b-gguf-pytorch-default-v1/gpt_oss/gpt-oss-20b-Q4_K_M.gguf"
    ).is_file()
    checks["gemma_present"] = (
        PROJECT_ROOT
        / "model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
    ).is_file()
    checks["output_configured"] = OUTPUT_DIR.is_absolute() and OUTPUT_DIR.is_dir()
    checks["credentials_cleared"] = not any(
        os.environ.get(name)
        for name in (
            "OPENAI_API_KEY",
            "KAGGLE_KEY",
            "KAGGLE_USERNAME",
            "HF_TOKEN",
            "HUGGING_FACE_HUB_TOKEN",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "GH_TOKEN",
            "GITHUB_TOKEN",
        )
    )

    try:
        socket.create_connection(("127.0.0.1", 9), timeout=0.1)
    except PermissionError as error:
        checks["python_network_denied"] = True
        details["network_error"] = str(error)
    except OSError as error:
        checks["python_network_denied"] = False
        details["network_error"] = f"Bloqueo no atribuible al hook: {error}"
    else:
        checks["python_network_denied"] = False
        details["network_error"] = "La conexion no fue bloqueada"

    if checks["output_configured"]:
        probe = OUTPUT_DIR / ".write-probe"
        try:
            probe.write_text("ok\n", encoding="utf-8")
            checks["output_writable"] = probe.read_text(encoding="utf-8") == "ok\n"
        finally:
            probe.unlink(missing_ok=True)
    else:
        checks["output_writable"] = False

    try:
        import llama_cpp

        checks["llama_cpp_import"] = True
        details["llama_cpp_version"] = str(getattr(llama_cpp, "__version__", "unknown"))
    except Exception as error:  # pragma: no cover - diagnostic path
        checks["llama_cpp_import"] = False
        details["llama_cpp_error"] = f"{type(error).__name__}: {error}"

    report = {
        "ok": all(checks.values()),
        "checks": checks,
        "details": details,
        "hostname": socket.gethostname(),
        "network_mode": os.environ.get("SANDBOX_NETWORK_MODE", "unknown"),
    }
    if checks["output_configured"]:
        (OUTPUT_DIR / "self_test_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
