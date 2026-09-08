#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

ACTION="${1:-start}"
CONFIG_PATH="${2:-}"

case "$ACTION" in
  ci)
    exec .venv/bin/python scripts/run_ci.py
    ;;
  prepare-mobile-apk)
    exec .venv/bin/python scripts/prepare_android_apk.py --output-root artifacts/mobile-ci
    ;;
  mobile-ci)
    if [[ -z "$CONFIG_PATH" ]]; then
      echo "Usage: bash platform.sh mobile-ci config/mobile-ci.emulator.yaml" >&2
      exit 2
    fi
    task_root="reports/mobile-ci/task-runs/cli-$(date +%s)-$RANDOM"
    mkdir -p "$task_root"
    export AUTOTEST_MOBILE_CONFIG="$CONFIG_PATH"
    export AUTOTEST_MOBILE_REPORT_ROOT="$ROOT/reports/mobile-ci"
    export AUTOTEST_MOBILE_SCENARIOS="${AUTOTEST_MOBILE_SCENARIOS:-[]}"
    export AUTOTEST_MOBILE_DEVICES="${AUTOTEST_MOBILE_DEVICES:-[]}"
    set +e
    .venv/bin/python -m pytest -q -s --tb=short \
      --basetemp "$task_root/pytest-work" \
      --junitxml "$task_root/pytest-junit.xml" \
      mobile/pytest_runtime.py 2>&1 | tee "$task_root/pytest-console.log"
    pytest_exit=${PIPESTATUS[0]}
    set -e
    set +e
    .venv/bin/python scripts/mobile_pytest_evidence.py \
      --report-root "$AUTOTEST_MOBILE_REPORT_ROOT" \
      --console "$task_root/pytest-console.log" \
      --junit "$task_root/pytest-junit.xml" \
      --exit-code "$pytest_exit"
    evidence_exit=$?
    set -e
    if [[ "$pytest_exit" -ne 0 ]]; then
      exit "$pytest_exit"
    fi
    exit "$evidence_exit"
    ;;
  *)
    echo "Unsupported Linux platform action: $ACTION" >&2
    exit 2
    ;;
esac
