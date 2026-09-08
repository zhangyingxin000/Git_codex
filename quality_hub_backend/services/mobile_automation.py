from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

import yaml

from scripts.mobile_pytest_evidence import finalize_mobile_pytest_run
from scripts.run_mobile_ci import (
    build_coverage_scope,
    expand,
    find_adb,
    http_json,
    load_mobile_assets,
    merge_device_sources,
    parse_adb_devices,
    parse_device_inventory,
)


class MobileAutomationService:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.default_config = self.root / "config" / "mobile-ci.local.yaml"
        self.report_root = self.root / "reports" / "mobile-ci"

    def _project_file(self, value: str, default: Path) -> Path:
        candidate = Path(value) if value else default
        resolved = candidate.resolve() if candidate.is_absolute() else (self.root / candidate).resolve()
        if self.root not in resolved.parents:
            raise ValueError("mobile configuration must stay inside the project")
        return resolved

    def _config(self, value: str = "") -> tuple[Path, dict[str, Any]]:
        path = self._project_file(value, self.default_config)
        if not path.is_file():
            return path, {}
        config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if str(config.get("schema_version") or "") != "1.0":
            raise ValueError("mobile CI schema_version must be 1.0")
        return path, load_mobile_assets(config, path, self.root)

    @staticmethod
    def _scenario(item: dict[str, Any]) -> dict[str, Any]:
        steps = item.get("steps") or []
        actions = {str(step.get("action") or "") for step in steps if isinstance(step, dict)}
        required = sorted(
            {
                str(name)
                for step in steps
                if isinstance(step, dict)
                for name in (
                    [step.get("requires")]
                    if isinstance(step.get("requires"), str)
                    else step.get("requires") or []
                )
                if name
            }
        )
        return {
            "id": str(item.get("id") or "mobile-workflow"),
            "name": str(item.get("name") or item.get("id") or "Mobile workflow"),
            "category": str(item.get("category") or "business"),
            "tags": item.get("tags") or [],
            "enabled": item.get("enabled", False) is True,
            "step_count": len(steps),
            "mutates_data": any(bool(step.get("mutates_data")) for step in steps if isinstance(step, dict)),
            "high_risk": any(
                str(step.get("risk_level") or "").lower() == "high"
                for step in steps
                if isinstance(step, dict)
            ),
            "requires_emulator": bool(
                actions.intersection(
                    {"network_off", "network_on", "network_profile", "network_restore", "incoming_call"}
                )
            ),
            "required_environment": required,
        }

    def _devices(self, config: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        pool = config.get("device_pool") or {}
        if not isinstance(pool, dict):
            return "", []
        server_mode = str(config.get("server_mode") or "managed").strip().lower()
        source = str(
            pool.get("source") or ("inventory" if server_mode == "external" else "adb")
        ).strip().lower()
        adb = find_adb(str(config.get("adb_path") or ""))
        adb_devices: list[dict[str, Any]] = []
        if adb and source in {"adb", "hybrid"}:
            completed = subprocess.run(
                [adb, "devices", "-l"],
                cwd=self.root,
                capture_output=True,
                text=True,
                errors="replace",
                check=False,
            )
            if completed.returncode == 0:
                adb_devices = parse_adb_devices(completed.stdout)
                for device in adb_devices:
                    device["source"] = "adb"
        inventory_value: Any = pool.get("inventory") or []
        if os.environ.get("AUTOTEST_MOBILE_DEVICE_INVENTORY", "").strip():
            inventory_value = os.environ["AUTOTEST_MOBILE_DEVICE_INVENTORY"]
        inventory = (
            parse_device_inventory(inventory_value)
            if source in {"inventory", "hybrid"}
            else []
        )
        return adb or "", merge_device_sources(adb_devices, inventory)

    @staticmethod
    def _performance_alerts(summary: dict[str, Any]) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for device in summary.get("device_results") or []:
            diagnosis = ((device.get("performance") or {}).get("diagnosis") or {})
            failed_checks = [
                {
                    "name": check.get("name") or "performance_check",
                    "actual": check.get("actual"),
                    "limit": check.get("limit"),
                }
                for check in diagnosis.get("checks") or []
                if str(check.get("status") or "").upper() == "FAIL"
            ]
            if failed_checks:
                alerts.append(
                    {
                        "udid": device.get("udid") or "",
                        "model": device.get("model") or "",
                        "failed_checks": failed_checks,
                    }
                )
        return alerts

    def _latest_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        if not self.report_root.is_dir():
            return []
        runs: list[dict[str, Any]] = []
        for directory in sorted(
            (
                item
                for item in self.report_root.iterdir()
                if item.is_dir() and (item / "summary.json").is_file()
            ),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )[:limit]:
            summary_path = directory / "summary.json"
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            performance_alerts = self._performance_alerts(summary)
            raw_status = str(summary.get("status") or "UNKNOWN")
            runs.append(
                {
                    "run_id": summary.get("run_id") or directory.name,
                    "status": raw_status,
                    "quality_status": (
                        "PASSED_WITH_WARNINGS"
                        if raw_status == "PASSED" and performance_alerts
                        else raw_status
                    ),
                    "performance_alerts": performance_alerts,
                    "message": summary.get("message") or summary.get("reason") or "",
                    "started_at": summary.get("started_at") or "",
                    "finished_at": summary.get("finished_at") or "",
                    "summary_url": f"/reports/mobile-ci/{directory.name}/summary.json",
                    "allure_url": f"/reports/mobile-ci/{directory.name}/allure-report/index.html",
                    "pytest_evidence_url": (
                        f"/reports/mobile-ci/{directory.name}/pytest-evidence.json"
                        if (directory / "pytest-evidence.json").is_file()
                        else ""
                    ),
                    "coverage_url": (
                        f"/reports/mobile-ci/{directory.name}/coverage-scope.json"
                        if (directory / "coverage-scope.json").is_file()
                        else ""
                    ),
                }
            )
        return runs

    def catalog(self, config_path: str = "") -> dict[str, Any]:
        path, config = self._config(config_path)
        adb, devices = self._devices(config)
        server_mode = str(config.get("server_mode") or "managed").strip().lower()
        pool = config.get("device_pool") or {}
        device_source = str(
            pool.get("source")
            or ("inventory" if server_mode == "external" else "adb")
        ).strip().lower() if isinstance(pool, dict) else "adb"
        appium = self.root / "node_modules" / ".bin" / "appium.cmd"
        allure = self.root / "node_modules" / ".bin" / "allure.cmd"
        environment = os.environ.copy()
        server_ready = server_mode != "external"
        resolved_server_url = ""
        resolved_status_url = ""
        if server_mode == "external":
            try:
                resolved_server_url = str(
                    expand(str(config.get("server_url") or ""), environment)
                ).strip().rstrip("/")
                status_value = str(config.get("server_status_url") or "").strip()
                resolved_status_url = str(
                    expand(status_value, environment)
                    if status_value
                    else f"{resolved_server_url}/status"
                ).strip()
                if resolved_server_url and resolved_status_url:
                    status_payload = http_json(resolved_status_url, timeout_seconds=2)
                    server_ready = (
                        (status_payload.get("value") or {}).get("ready") is True
                    )
            except (OSError, ValueError, TypeError):
                server_ready = False
        app_value = str((config.get("capabilities") or {}).get("appium:app") or "")
        try:
            resolved_app = str(expand(app_value, environment)) if app_value else ""
        except ValueError:
            resolved_app = ""
        apk_ready = bool(
            resolved_app
            and (Path(resolved_app).is_file() or server_mode == "external")
        )
        installed_package = str((config.get("capabilities") or {}).get("appium:appPackage") or "").strip()
        target_ready = apk_ready or bool(installed_package)
        blockers = []
        if not path.is_file():
            blockers.append("移动端配置不存在")
        if server_mode == "external" and not resolved_server_url:
            blockers.append("未配置可访问的Grid地址")
        elif server_mode == "external" and not server_ready:
            blockers.append("Selenium/Appium Grid当前不可访问")
        elif server_mode != "external" and not appium.is_file():
            blockers.append("Appium CLI尚未安装")
        if not allure.is_file():
            blockers.append("Allure CLI尚未安装")
        if device_source in {"adb", "hybrid"} and not adb:
            blockers.append("ADB尚未配置")
        elif not devices:
            blockers.append(
                "Grid设备清单为空"
                if device_source == "inventory"
                else "未发现已连接的真机或模拟器"
            )
        if not target_ready:
            blockers.append("未提供APK，且未配置已安装应用包名")
        pages = config.get("pages") or {}
        return {
            "status": "READY" if not blockers else "BLOCKED",
            "blockers": blockers,
            "config_path": str(path.relative_to(self.root)) if path.is_file() else str(path),
            "config_exists": path.is_file(),
            "server_mode": server_mode,
            "server_ready": server_ready,
            "device_source": device_source,
            "appium_ready": appium.is_file() if server_mode != "external" else server_ready,
            "allure_ready": allure.is_file(),
            "adb_path": adb,
            "devices": devices,
            "apk_path": resolved_app,
            "apk_ready": apk_ready,
            "installed_package": installed_package,
            "target_ready": target_ready,
            "page_objects": [
                {"name": name, "element_count": len(elements) if isinstance(elements, dict) else 0}
                for name, elements in pages.items()
            ],
            "scenarios": [self._scenario(item) for item in config.get("workflows") or []],
            "coverage": build_coverage_scope(
                config,
                config.get("workflows") or [],
                config.get("safety") or {},
            ),
            "latest_runs": self._latest_runs(),
        }

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        options = payload.get("options") if isinstance(payload.get("options"), dict) else {}
        context = payload.get("_task_context") if isinstance(payload.get("_task_context"), dict) else {}
        progress = context.get("progress") if callable(context.get("progress")) else None
        is_cancelled = context.get("is_cancelled") if callable(context.get("is_cancelled")) else None
        config_path, _ = self._config(str(options.get("config_path") or ""))
        if not config_path.is_file():
            return {"status": "BLOCKED", "message": f"移动端配置不存在：{config_path}"}
        python = self.root / ".venv" / "Scripts" / "python.exe"
        runner = self.root / "mobile" / "pytest_runtime.py"
        if not python.is_file() or not runner.is_file():
            return {"status": "BLOCKED", "message": "移动端运行环境尚未安装完整。"}

        environment = os.environ.copy()
        environment.update(
            {
                "AUTOTEST_MOBILE_CONFIG": str(config_path),
                "AUTOTEST_MOBILE_REPORT_ROOT": str(self.report_root),
                "AUTOTEST_MOBILE_SCENARIOS": json.dumps(options.get("scenarios") or []),
                "AUTOTEST_MOBILE_DEVICES": json.dumps(options.get("devices") or []),
                "PYTHONUTF8": "1",
            }
        )
        apk_path = str(options.get("apk_path") or "").strip()
        if apk_path:
            apk = Path(apk_path)
            if not apk.is_file():
                return {"status": "BLOCKED", "message": f"APK文件不存在：{apk}"}
            environment["AUTOTEST_ANDROID_APP"] = str(apk)
        if progress:
            progress({"phase": "mobile", "percent": 10, "message": "正在启动 pytest 移动端任务"})
        self.report_root.mkdir(parents=True, exist_ok=True)
        task_name = re.sub(
            r"[^A-Za-z0-9_.-]+",
            "-",
            str(context.get("task_id") or f"manual-{uuid.uuid4().hex}"),
        ).strip("-")
        task_root = self.report_root / "task-runs" / (task_name or f"manual-{uuid.uuid4().hex}")
        task_root.mkdir(parents=True, exist_ok=False)
        pytest_work = task_root / "pytest-work"
        console_path = task_root / "pytest-console.log"
        junit_path = task_root / "pytest-junit.xml"
        command = [
            str(python),
            "-m",
            "pytest",
            "-q",
            "-s",
            "--tb=short",
            "--basetemp",
            str(pytest_work),
            "--junitxml",
            str(junit_path),
            str(runner),
        ]
        process: subprocess.Popen[str] | None = None
        try:
            with console_path.open("w", encoding="utf-8", errors="replace") as log_file:
                process = subprocess.Popen(
                    command,
                    cwd=self.root,
                    env=environment,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    errors="replace",
                )
                last_progress = 0.0
                while process.poll() is None:
                    if is_cancelled and is_cancelled():
                        self._stop_process_tree(process)
                        return {
                            "status": "CANCELLED",
                            "message": "移动端任务已停止。",
                            "pytest_console_url": (
                                f"/reports/mobile-ci/task-runs/{task_root.name}/pytest-console.log"
                            ),
                        }
                    now = time.monotonic()
                    if progress and now - last_progress >= 2:
                        progress({"phase": "mobile", "percent": 60, "message": "pytest 正在调度 Appium 设备场景"})
                        last_progress = now
                    time.sleep(0.25)
            output = console_path.read_text(encoding="utf-8", errors="replace")
        finally:
            if pytest_work.is_dir():
                shutil.rmtree(pytest_work, ignore_errors=True)
        if process is None:
            return {"status": "FAILED", "message": "移动端任务未能启动。"}
        try:
            finalized = finalize_mobile_pytest_run(
                self.report_root,
                console_path,
                junit_path,
                int(process.returncode or 0),
            )
        except Exception as exc:
            return {
                "status": "FAILED",
                "message": f"移动端任务未能归档 pytest 证据：{type(exc).__name__}: {exc}",
                "exit_code": process.returncode,
                "output": output[-4000:],
                "pytest_console_url": (
                    f"/reports/mobile-ci/task-runs/{task_root.name}/pytest-console.log"
                ),
            }
        summary_path = Path(finalized["summary_path"])
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        relative_run = summary_path.parent.relative_to(self.report_root)
        performance_alerts = self._performance_alerts(summary)
        raw_status = str(summary.get("status") or ("PASSED" if process.returncode == 0 else "FAILED"))
        quality_status = (
            "PASSED_WITH_WARNINGS"
            if raw_status == "PASSED" and performance_alerts
            else raw_status
        )
        message = str(summary.get("message") or "移动端任务执行完成。")
        if performance_alerts:
            message = f"{message}；功能场景通过，但有 {len(performance_alerts)} 台设备存在性能阈值提醒。"
        if progress:
            progress({"phase": "complete", "percent": 100, "message": "移动端报告已生成"})
        return {
            "status": quality_status,
            "execution_status": raw_status,
            "message": message,
            "run_id": summary.get("run_id") or relative_run.name,
            "summary_url": f"/reports/mobile-ci/{relative_run.as_posix()}/summary.json",
            "allure_url": f"/reports/mobile-ci/{relative_run.as_posix()}/allure-report/index.html",
            "pytest_evidence_url": (
                f"/reports/mobile-ci/{relative_run.as_posix()}/pytest-evidence.json"
            ),
            "pytest_console_url": (
                f"/reports/mobile-ci/{relative_run.as_posix()}/pytest-console.log"
            ),
            "coverage_url": (
                f"/reports/mobile-ci/{relative_run.as_posix()}/coverage-scope.json"
            ),
            "devices": summary.get("devices") or [],
            "device_results": summary.get("device_results") or [],
            "coverage": summary.get("coverage") or {},
            "performance_alerts": performance_alerts,
        }

    @staticmethod
    def _stop_process_tree(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                check=False,
            )
            return
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
