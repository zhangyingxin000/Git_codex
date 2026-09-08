#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ "${1:-}" != "--skip-ci-setup" ]]; then
  bash setup-ci.sh
fi

export APPIUM_HOME="$ROOT/.appium"
export npm_config_cache="$ROOT/.npm-cache"
if ! node_modules/.bin/appium driver list --installed | grep -q uiautomator2; then
  node_modules/.bin/appium driver install uiautomator2
fi

echo "Linux Android Appium environment is ready."
