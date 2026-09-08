from __future__ import annotations

import json
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from quality_hub_backend.api.routes.mobile import build_mobile_router
from quality_hub_backend.handlers import TaskDispatcher
from quality_hub_backend.services.mobile_automation import MobileAutomationService


def test_mobile_catalog_exposes_devices_page_objects_and_scenarios(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "node_modules" / ".bin").mkdir(parents=True)
    (tmp_path / "node_modules" / ".bin" / "appium.cmd").touch()
    (tmp_path / "node_modules" / ".bin" / "allure.cmd").touch()
    (tmp_path / "mobile" / "pages").mkdir(parents=True)
    (tmp_path / "mobile" / "scenarios").mkdir(parents=True)
    (tmp_path / "config").mkdir()
    apk = tmp_path / "sample.apk"
    apk.touch()
    (tmp_path / "mobile" / "pages" / "sample.yaml").write_text(
        'schema_version: "1.0"\npages:\n  login:\n    submit:\n'
        '      by: id\n      value: sample:id/login\n',
        encoding="utf-8",
    )
    (tmp_path / "mobile" / "scenarios" / "sample.yaml").write_text(
        'schema_version: "1.0"\nworkflows:\n  - id: login-smoke\n'
        '    name: Login smoke\n    enabled: true\n    steps:\n'
        '      - name: Submit\n        action: click\n        target: login.submit\n',
        encoding="utf-8",
    )
    config = {
        "schema_version": "1.0",
        "enabled": True,
        "capabilities": {"appium:app": str(apk)},
        "page_object_files": ["mobile/pages/sample.yaml"],
        "scenario_files": ["mobile/scenarios/sample.yaml"],
    }
    (tmp_path / "config" / "mobile-ci.local.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True),
        encoding="utf-8",
    )
    latest = tmp_path / "reports" / "mobile-ci" / "mobile-latest"
    latest.mkdir(parents=True)
    (latest / "summary.json").write_text(
        json.dumps(
            {
                "run_id": "mobile-latest",
                "status": "PASSED",
                "device_results": [
                    {
                        "udid": "emulator-5554",
                        "performance": {
                            "diagnosis": {
                                "checks": [
                                    {"name": "process_cpu_percent", "actual": 74, "limit": 60, "status": "FAIL"}
                                ]
                            }
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    service = MobileAutomationService(tmp_path)
    monkeypatch.setattr(
        service,
        "_devices",
        lambda _: (
            "C:/Android/platform-tools/adb.exe",
            [{"udid": "emulator-5554", "model": "Pixel_8", "kind": "emulator"}],
        ),
    )

    catalog = service.catalog()

    assert catalog["status"] == "READY"
    assert catalog["apk_ready"] is True
    assert catalog["devices"][0]["udid"] == "emulator-5554"
    assert catalog["page_objects"] == [{"name": "login", "element_count": 1}]
    assert catalog["scenarios"][0]["id"] == "login-smoke"
    assert catalog["scenarios"][0]["step_count"] == 1
    assert catalog["latest_runs"][0]["quality_status"] == "PASSED_WITH_WARNINGS"
    assert catalog["latest_runs"][0]["performance_alerts"][0]["failed_checks"][0]["name"] == "process_cpu_percent"


def test_mobile_catalog_accepts_external_grid_inventory_without_local_appium_or_adb(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / "node_modules" / ".bin").mkdir(parents=True)
    (tmp_path / "node_modules" / ".bin" / "allure.cmd").touch()
    (tmp_path / "config").mkdir()
    config = {
        "schema_version": "1.0",
        "enabled": True,
        "server_mode": "external",
        "server_url": "http://grid:4444/wd/hub",
        "device_pool": {
            "source": "inventory",
            "mode": "all",
            "inventory": [
                {
                    "udid": "emulator-5554",
                    "model": "Pixel_8_API_35",
                    "kind": "emulator",
                }
            ],
        },
        "capabilities": {
            "platformName": "Android",
            "appium:app": "https://downloads.example.com/app.apk",
        },
    }
    (tmp_path / "config" / "mobile-ci.local.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "quality_hub_backend.services.mobile_automation.http_json",
        lambda *args, **kwargs: {"value": {"ready": True}},
    )

    catalog = MobileAutomationService(tmp_path).catalog()

    assert catalog["status"] == "READY"
    assert catalog["server_mode"] == "external"
    assert catalog["device_source"] == "inventory"
    assert catalog["appium_ready"] is True
    assert catalog["server_ready"] is True
    assert catalog["apk_ready"] is True
    assert catalog["devices"][0]["source"] == "inventory"


class FakeMobileAutomation:
    def __init__(self) -> None:
        self.payload = None

    def catalog(self, config_path: str = "") -> dict:
        return {"status": "READY", "config_path": config_path}

    def run(self, payload: dict) -> dict:
        self.payload = payload
        return {"status": "PASSED", "run_id": "mobile-test"}


def test_mobile_router_returns_catalog() -> None:
    service = FakeMobileAutomation()
    app = FastAPI()
    app.router.routes.extend(build_mobile_router(service).routes)

    response = TestClient(app).get("/api/mobile/catalog", params={"config_path": "config/test.yaml"})

    assert response.status_code == 200
    assert response.json() == {"status": "READY", "config_path": "config/test.yaml"}


def test_task_dispatcher_registers_mobile_appium_handler() -> None:
    service = FakeMobileAutomation()
    dispatcher = TaskDispatcher(object(), mobile_automation=service)
    payload = {"options": {"scenarios": ["login-smoke"], "devices": ["emulator-5554"]}}

    result = dispatcher.resolve("mobile_appium")(payload)

    assert "mobile_appium" in dispatcher.task_types
    assert result == {"status": "PASSED", "run_id": "mobile-test"}
    assert service.payload == payload
