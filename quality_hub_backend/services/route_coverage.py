from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.routing import APIRoute


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _priority(path: str, methods: list[str]) -> str:
    if path in {"/api/health", "/api/tasks", "/api/tasks/{task_id}"}:
        return "P0"
    if any(token in path for token in ("/pipeline/", "/newman/", "/pytest/", "/jmeter", "/mysql/")):
        return "P0"
    if "POST" in methods or "PUT" in methods or "DELETE" in methods:
        return "P1"
    return "P2"


def _scope(path: str) -> str:
    if path == "/api/health" or path.startswith("/api/tasks") or "/pipeline/" in path:
        return "demo-critical"
    if any(token in path for token in ("/newman/", "/pytest/", "/jmeter", "/mysql/")):
        return "integration-required"
    return "standard"


def _test_sources(test_root: Path) -> tuple[str, dict[str, str]]:
    sources = {}
    for path in sorted(test_root.glob("test_*.py")):
        sources[path.name] = path.read_text(encoding="utf-8")
    return "\n".join(sources.values()), sources


def _path_evidence(path: str, sources: dict[str, str]) -> list[str]:
    literal = re.sub(r"\{[^}]+\}", "", path).rstrip("/")
    evidence = []
    for name, source in sources.items():
        if path in source or (len(literal) >= 8 and literal in source):
            evidence.append(name)
    return evidence


def _api_routes(routes: list[Any]):
    for route in routes:
        if isinstance(route, APIRoute):
            yield route
            continue
        original_router = getattr(route, "original_router", None)
        nested = getattr(original_router, "routes", None)
        if nested:
            yield from _api_routes(list(nested))


def build_route_coverage(application: Any, test_root: Path) -> dict[str, Any]:
    all_test_text, sources = _test_sources(test_root)
    routes = []
    seen = set()
    for route in _api_routes(list(application.routes)):
        if not route.path.startswith("/api/"):
            continue
        methods = sorted(method for method in route.methods if method not in {"HEAD", "OPTIONS"})
        key = (route.path, tuple(methods))
        if key in seen:
            continue
        seen.add(key)
        endpoint_name = getattr(route.endpoint, "__name__", "")
        evidence = _path_evidence(route.path, sources)
        handler_referenced = bool(endpoint_name and endpoint_name in all_test_text)
        scope = _scope(route.path)
        status = (
            "COVERED"
            if evidence or handler_referenced
            else "INTEGRATION_REQUIRED"
            if scope == "integration-required"
            else "UNMAPPED"
        )
        routes.append(
            {
                "path": route.path,
                "methods": methods,
                "name": route.name,
                "handler": endpoint_name,
                "tags": list(route.tags or []),
                "priority": _priority(route.path, methods),
                "coverage_status": status,
                "evidence": evidence or (["handler-reference"] if handler_referenced else []),
                "scope": scope,
            }
        )
    counts = {
        "routes": len(routes),
        "covered": sum(row["coverage_status"] == "COVERED" for row in routes),
        "unmapped": sum(row["coverage_status"] == "UNMAPPED" for row in routes),
        "integration_required": sum(
            row["coverage_status"] == "INTEGRATION_REQUIRED" for row in routes
        ),
        "p0": sum(row["priority"] == "P0" for row in routes),
        "p0_unmapped": sum(
            row["priority"] == "P0" and row["coverage_status"] == "UNMAPPED" for row in routes
        ),
    }
    return {
        "schema_version": "1.0",
        "generated_at": _now(),
        "method": "static route and test-reference analysis",
        "summary": counts,
        "routes": routes,
    }


def write_route_coverage(application: Any, test_root: Path, output_root: Path) -> dict[str, Any]:
    payload = build_route_coverage(application, test_root)
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / "route-test-coverage.json"
    markdown_path = output_root / "route-test-coverage.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = payload["summary"]
    lines = [
        "# Route Test Coverage",
        "",
        f"- Routes: {summary['routes']}",
        f"- Covered by static evidence: {summary['covered']}",
        f"- Unmapped: {summary['unmapped']}",
        f"- Integration required: {summary['integration_required']}",
        f"- P0 routes: {summary['p0']}",
        f"- P0 unmapped: {summary['p0_unmapped']}",
        "",
        "| Priority | Methods | Path | Coverage | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["routes"]:
        lines.append(
            f"| {row['priority']} | {','.join(row['methods'])} | `{row['path']}` | "
            f"{row['coverage_status']} | {', '.join(row['evidence']) or '-'} |"
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {**payload, "json_path": str(json_path), "markdown_path": str(markdown_path)}
