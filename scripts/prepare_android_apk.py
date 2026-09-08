from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "local"


def source_label(source: str) -> str:
    parsed = urllib.parse.urlsplit(source)
    if parsed.scheme in {"http", "https"}:
        hostname = parsed.hostname or ""
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        netloc = f"{hostname}:{parsed.port}" if parsed.port else hostname
        return urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
    return str(Path(source).expanduser().resolve())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_apk(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"APK is empty or missing: {path}")
    if not zipfile.is_zipfile(path):
        raise ValueError("Downloaded artifact is not an APK/ZIP file; use a direct APK URL")
    with zipfile.ZipFile(path) as archive:
        if "AndroidManifest.xml" not in archive.namelist():
            raise ValueError("APK does not contain AndroidManifest.xml")


def find_aapt() -> Path | None:
    sdk_roots = [
        Path(value)
        for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT")
        if (value := os.environ.get(name))
    ]
    if os.environ.get("LOCALAPPDATA"):
        sdk_roots.append(Path(os.environ["LOCALAPPDATA"]) / "Android" / "Sdk")
    for sdk_root in sdk_roots:
        build_tools = sdk_root / "build-tools"
        if not build_tools.is_dir():
            continue
        for version_dir in sorted(build_tools.iterdir(), reverse=True):
            for name in ("aapt2.exe", "aapt.exe", "aapt2", "aapt"):
                candidate = version_dir / name
                if candidate.is_file():
                    return candidate
    executable = shutil.which("aapt2") or shutil.which("aapt")
    return Path(executable) if executable else None


def inspect_apk(path: Path) -> dict[str, str]:
    aapt = find_aapt()
    if not aapt:
        return {}
    completed = subprocess.run(
        [str(aapt), "dump", "badging", str(path)],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        return {}
    first_line = completed.stdout.splitlines()[0] if completed.stdout else ""
    values = {
        key: value
        for key, value in re.findall(
            r"(?:^|\s)(name|versionCode|versionName)='([^']*)'", first_line
        )
    }
    return {
        "package_name": values.get("name", ""),
        "version_code": values.get("versionCode", ""),
        "version_name": values.get("versionName", ""),
    }


def acquire_apk(
    source: str,
    output_root: Path,
    build_id: str,
    *,
    expected_sha256: str = "",
    authorization: str = "",
) -> dict[str, object]:
    source = source.strip()
    if not source:
        raise ValueError("APK source is required")
    run_root = output_root / "runs" / safe_name(build_id)
    run_root.mkdir(parents=True, exist_ok=False)
    target = run_root / "app-under-test.apk"
    parsed = urllib.parse.urlsplit(source)
    source_type = "url" if parsed.scheme in {"http", "https"} else "file"
    if source_type == "url":
        request = urllib.request.Request(source, headers={"User-Agent": "AutoTest-AI/1.0"})
        if authorization:
            request.add_header("Authorization", authorization)
        with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as output:
            shutil.copyfileobj(response, output)
    else:
        local_source = Path(source).expanduser().resolve()
        if not local_source.is_file():
            raise FileNotFoundError(f"APK source does not exist: {local_source}")
        shutil.copy2(local_source, target)

    validate_apk(target)
    digest = sha256_file(target)
    if expected_sha256 and digest.lower() != expected_sha256.strip().lower():
        raise ValueError(f"APK SHA-256 mismatch: expected {expected_sha256}, got {digest}")

    metadata: dict[str, object] = {
        "schema_version": "1.0",
        "build_id": safe_name(build_id),
        "source_type": source_type,
        "source": source_label(source),
        "apk_path": str(target.resolve()),
        "size_bytes": target.stat().st_size,
        "sha256": digest,
        "acquired_at": datetime.now(UTC).isoformat(timespec="seconds"),
        **inspect_apk(target),
    }
    metadata_path = run_root / "apk-metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "current-apk.path").write_text(str(target.resolve()), encoding="utf-8")
    (output_root / "current-apk-metadata.path").write_text(
        str(metadata_path.resolve()), encoding="utf-8"
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire and validate an immutable Android APK.")
    parser.add_argument("--source", default=os.environ.get("AUTOTEST_ANDROID_APK_SOURCE", ""))
    parser.add_argument("--output-root", type=Path, default=ROOT / "artifacts" / "mobile-ci")
    parser.add_argument(
        "--build-id",
        default=os.environ.get("BUILD_TAG") or datetime.now().strftime("local-%Y%m%d-%H%M%S"),
    )
    parser.add_argument(
        "--expected-sha256", default=os.environ.get("AUTOTEST_ANDROID_APK_SHA256", "")
    )
    args = parser.parse_args()
    authorization = os.environ.get("AUTOTEST_ANDROID_APK_AUTHORIZATION", "")
    metadata = acquire_apk(
        args.source,
        args.output_root if args.output_root.is_absolute() else ROOT / args.output_root,
        args.build_id,
        expected_sha256=args.expected_sha256,
        authorization=authorization,
    )
    print(f"APK ready: {metadata['apk_path']}")
    print(f"SHA-256: {metadata['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
