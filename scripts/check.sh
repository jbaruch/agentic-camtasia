#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")/.."
uv sync --extra verification --locked
ruff check skills hooks tests scripts
ruff format --check skills hooks tests scripts
pyright
uv run --extra verification --locked python -B -m unittest discover -s tests -v
uv run --locked python -B scripts/check_distribution.py .
