from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.run_mobile_ci import ROOT, main as run_mobile_ci


def _json_list(name: str) -> list[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return []
    value = json.loads(raw)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{name} must be a JSON string array")
    return [item for item in value if item.strip()]


def test_mobile_appium_runtime() -> None:
    config = os.environ.get("AUTOTEST_MOBILE_CONFIG", "").strip()
    if not config:
        raise AssertionError("AUTOTEST_MOBILE_CONFIG is required")

    report_root = os.environ.get(
        "AUTOTEST_MOBILE_REPORT_ROOT",
        str(ROOT / "reports" / "mobile-ci"),
    )
    arguments = ["--config", config, "--report-root", report_root]
    for scenario in _json_list("AUTOTEST_MOBILE_SCENARIOS"):
        arguments.extend(["--scenario", scenario])
    for device in _json_list("AUTOTEST_MOBILE_DEVICES"):
        arguments.extend(["--device", device])

    exit_code = run_mobile_ci(arguments)
    assert exit_code == 0, "Android Appium execution did not pass; inspect the generated mobile report"
