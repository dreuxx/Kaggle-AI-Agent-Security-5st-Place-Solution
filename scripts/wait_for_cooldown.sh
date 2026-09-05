#!/usr/bin/env bash
set -euo pipefail

threshold_c="${1:-75}"
required_stable="${2:-3}"
stable=0

while true; do
    temp_c="$(sensors | awk '/Package id 0:/ {value=$4; gsub(/[^0-9.]/, "", value); print int(value); exit}')"
    if [[ -z "${temp_c}" ]]; then
        echo "No se pudo leer Package id 0" >&2
        exit 1
    fi
    printf '[%s] CPU package=%s C, objetivo<=%s C, estable=%s/%s\n' \
        "$(date -Is)" "${temp_c}" "${threshold_c}" "${stable}" "${required_stable}"
    if (( temp_c <= threshold_c )); then
        stable=$((stable + 1))
    else
        stable=0
    fi
    if (( stable >= required_stable )); then
        printf '\a[%s] COOLDOWN COMPLETO: CPU package=%s C\n' "$(date -Is)" "${temp_c}"
        exit 0
    fi
    sleep 15
done
