#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

.venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt -r requirements-ci.lock
npm ci --no-audit --no-fund
.venv/bin/python -m ruff --version
.venv/bin/detect-secrets --version
node_modules/.bin/allure --version
node_modules/.bin/appium --version

echo "Linux CI tools are ready."
