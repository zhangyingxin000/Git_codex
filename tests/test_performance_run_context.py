import json

import app


def _performance_report(p95=100, profile="baseline"):
    summary = {
        "requests": 100,
        "average_ms": 80,
        "p50_ms": 70,
        "p90_ms": 90,
        "p95_ms": p95,
        "p99_ms": 150,
        "max_ms": 200,
        "error_rate": 0,
        "request_throughput_rps": 10,
        "by_label": [{"label": "GET /health"}],
    }
    return {
        "report_type": "REQUIREMENT_PACKAGE_JMETER_RUN",
        "status": "PASSED",
        "summary_path": "reports/run/summary.json",
        "performance_summary": summary,
        "performance_gate": {"status": "PASSED", "profile": profile},
        "target_api": "health",
    }


def test_run_context_tracks_candidate_approval_and_regression(monkeypatch, tmp_path):
    package = {"package_id": "pkg", "name": "测试需求", "root": str(tmp_path)}
    monkeypatch.setattr(app, "requirement_package_by_id", lambda *_args: package)
    monkeypatch.setattr(app, "row", lambda *_args: {"id": "project", "base_url": "https://test.example"})

    app.create_requirement_run_context("project", "pkg", {"run_id": "run-1"})
    first = app.update_requirement_run_context(
        "project", "pkg", "run-1", "jmeter", "PASSED", _performance_report()
    )
    assert first["performance"]["baseline"]["status"] == "candidate"

    approved = app.approve_requirement_performance_baseline("project", "pkg", "run-1", "tester")
    assert approved["performance"]["baseline"]["status"] == "active"
    assert approved["baseline"] is True

    app.create_requirement_run_context("project", "pkg", {"run_id": "run-2"})
    second = app.update_requirement_run_context(
        "project", "pkg", "run-2", "jmeter", "PASSED", _performance_report(p95=130)
    )
    assert second["performance"]["comparison"]["result"] == "regressed"
    assert second["performance"]["comparison"]["reference_run_id"] == "run-1"

    persisted = json.loads((tmp_path / "runs" / "run-2" / "run-context.json").read_text(encoding="utf-8"))
    assert persisted["performance"]["comparison"]["result"] == "regressed"
