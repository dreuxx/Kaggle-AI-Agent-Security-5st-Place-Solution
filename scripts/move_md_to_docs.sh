#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_DIR="$ROOT_DIR/docs"

mkdir -p "$DOCS_DIR"

find "$ROOT_DIR" -maxdepth 1 -type f -name '*.md' ! -name 'AGENTS.md' -print0 |
  while IFS= read -r -d '' file; do
    mv "$file" "$DOCS_DIR/"
  done

echo "Markdown files moved to $DOCS_DIR"
