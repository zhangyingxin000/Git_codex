from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sdk_roots() -> list[Path]:
    roots = [
        Path(value)
        for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT")
        if (value := os.environ.get(name))
    ]
    if os.environ.get("LOCALAPPDATA"):
        roots.append(Path(os.environ["LOCALAPPDATA"]) / "Android" / "Sdk")
    return roots


def find_sdk_tool(relative_windows: str, relative_unix: str, fallback: str) -> Path:
    for root in sdk_roots():
        for relative in (relative_windows, relative_unix):
            candidate = root / relative
            if candidate.is_file():
                return candidate
    executable = shutil.which(fallback)
    if executable:
        return Path(executable)
    raise FileNotFoundError(f"Android SDK tool was not found: {fallback}")


def emulator_executable() -> Path:
    return find_sdk_tool("emulator/emulator.exe", "emulator/emulator", "emulator")


def adb_executable() -> Path:
    return find_sdk_tool("platform-tools/adb.exe", "platform-tools/adb", "adb")


def list_avds(emulator: Path | None = None) -> list[str]:
    executable = emulator or emulator_executable()
    completed = subprocess.run(
        [str(executable), "-list-avds"],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Unable to list Android AVDs")
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def build_emulator_command(
    executable: Path,
    avd_name: str,
    port: int,
    *,
    headless: bool = True,
    wipe_data: bool = False,
) -> list[str]:
    command = [
        str(executable),
        "-avd",
        avd_name,
        "-port",
        str(port),
        "-no-audio",
        "-no-boot-anim",
        "-gpu",
        "swiftshader_indirect",
    ]
    if headless:
        command.append("-no-window")
    if wipe_data:
        command.append("-wipe-data")
    return command


def adb_value(adb: Path, udid: str, arguments: list[str]) -> str:
    completed = subprocess.run(
        [str(adb), "-s", udid, *arguments],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def wait_for_boot(adb: Path, udid: str, timeout_seconds: int) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if adb_value(adb, udid, ["shell", "getprop", "sys.boot_completed"]) == "1":
            return True
        time.sleep(2)
    return False


def start_emulator(
    avd_name: str,
    port: int,
    state_path: Path,
    *,
    timeout_seconds: int = 300,
    headless: bool = True,
    wipe_data: bool = False,
) -> dict[str, Any]:
    if port < 5554 or port > 5682 or port % 2:
        raise ValueError("Android emulator port must be an even number between 5554 and 5682")
    emulator = emulator_executable()
    adb = adb_executable()
    available_avds = list_avds(emulator)
    if avd_name not in available_avds:
        raise ValueError(
            f"Android AVD was not found: {avd_name}; available: {', '.join(available_avds) or 'none'}"
        )
    udid = f"emulator-{port}"
    if adb_value(adb, udid, ["shell", "getprop", "sys.boot_completed"]) == "1":
        state = {
            "schema_version": "1.0",
            "status": "READY",
            "avd_name": avd_name,
            "udid": udid,
            "port": port,
            "started_by_runner": False,
            "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    state_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = state_path.with_suffix(".log")
    command = build_emulator_command(
        emulator, avd_name, port, headless=headless, wipe_data=wipe_data
    )
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" and headless else 0
    with log_path.open("wb") as log_handle:
        process = subprocess.Popen(
            command,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
        )
    if not wait_for_boot(adb, udid, timeout_seconds):
        process.terminate()
        raise TimeoutError(f"Android emulator did not finish booting: {udid}")
    state = {
        "schema_version": "1.0",
        "status": "READY",
        "avd_name": avd_name,
        "udid": udid,
        "port": port,
        "pid": process.pid,
        "started_by_runner": True,
        "log": str(log_path.resolve()),
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def stop_emulator(state_path: Path) -> dict[str, Any]:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("started_by_runner") is True:
        adb = adb_executable()
        subprocess.run(
            [str(adb), "-s", str(state["udid"]), "emu", "kill"],
            capture_output=True,
            check=False,
        )
        state["status"] = "STOPPED"
        state["stopped_at"] = datetime.now(UTC).isoformat(timespec="seconds")
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage a CI-owned Android Studio AVD.")
    subparsers = parser.add_subparsers(dest="action", required=True)
    subparsers.add_parser("list")
    start = subparsers.add_parser("start")
    start.add_argument("--avd", required=True)
    start.add_argument("--port", type=int, default=5554)
    start.add_argument("--state", type=Path, required=True)
    start.add_argument("--timeout", type=int, default=300)
    start.add_argument("--show-window", action="store_true")
    start.add_argument("--wipe-data", action="store_true")
    stop = subparsers.add_parser("stop")
    stop.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()

    if args.action == "list":
        print("\n".join(list_avds()))
        return 0
    state_path = args.state if args.state.is_absolute() else ROOT / args.state
    if args.action == "start":
        result = start_emulator(
            args.avd,
            args.port,
            state_path,
            timeout_seconds=args.timeout,
            headless=not args.show_window,
            wipe_data=args.wipe_data,
        )
    else:
        result = stop_emulator(state_path)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
