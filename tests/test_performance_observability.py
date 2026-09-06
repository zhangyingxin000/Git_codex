import json

from quality_hub_backend.services.performance_observability import (
    attach_observability_to_diagnosis,
    build_database_status_evidence,
    collect_observability_evidence,
    describe_observability_configuration,
)


def test_collect_observability_evidence_aligns_window_and_detects_signals(tmp_path):
    host_path = tmp_path / "host.json"
    database_path = tmp_path / "database.json"
    host_path.write_text(json.dumps({"cpu_percent_max": 91, "memory_percent_max": 70}), encoding="utf-8")
    database_path.write_text(json.dumps({"slow_query_count": 3, "max_lock_wait_ms": 350}), encoding="utf-8")

    evidence = collect_observability_evidence(
        tmp_path,
        options={
            "observability_files": {
                "host": host_path.name,
                "database": database_path.name,
            }
        },
        window_start_ms=1000,
        window_end_ms=5000,
    )

    assert evidence["status"] == "PARTIAL"
    assert evidence["window"] == {"start_ms": 1000, "end_ms": 5000}
    assert {item["signal"] for item in evidence["signals"]} == {
        "cpu_saturation",
        "slow_queries",
        "lock_wait",
    }

    diagnosis = attach_observability_to_diagnosis(
        {
            "findings": [],
            "evidence_boundary": {
                "requires_external_evidence": ["应用CPU/内存/GC", "数据库等待", "应用日志/APM"]
            },
        },
        evidence,
    )
    assert diagnosis["observability"]["status"] == "PARTIAL"
    assert diagnosis["evidence_boundary"]["requires_external_evidence"] == ["应用日志/APM"]
    assert diagnosis["bottleneck_hypotheses"][0]["confidence"] == "medium"


def test_database_status_evidence_uses_run_window_deltas():
    evidence = build_database_status_evidence(
        {
            "Threads_connected": "8",
            "Threads_running": "2",
            "Questions": "1000",
            "Slow_queries": "4",
            "Innodb_row_lock_waits": "10",
            "Innodb_row_lock_time": "300",
            "Connections": "200",
            "Aborted_connects": "1",
        },
        {
            "Threads_connected": "10",
            "Threads_running": "4",
            "Questions": "1120",
            "Slow_queries": "5",
            "Innodb_row_lock_waits": "12",
            "Innodb_row_lock_time": "480",
            "Connections": "205",
            "Aborted_connects": "2",
        },
    )

    assert evidence["questions_delta"] == 120
    assert evidence["slow_query_count"] == 1
    assert evidence["lock_wait_count"] == 2
    assert evidence["lock_wait_ms_total"] == 180
    assert evidence["aborted_connects_delta"] == 1


def test_database_status_errors_do_not_count_as_available_metrics():
    evidence = build_database_status_evidence(
        {"_error": "access denied"},
        {"_error": "access denied"},
    )

    assert evidence == {}


def test_observability_configuration_distinguishes_configured_from_collected():
    status = describe_observability_configuration(
        {
            "performance_observability": [
                {"type": "http_json", "category": "apm", "url_env": "APM_METRICS_URL"},
                {"type": "json_file", "category": "host", "path": "metrics/host.json"},
            ]
        },
        automatic_categories=("database",),
    )

    assert status["status"] == "COMPLETE"
    assert status["configured_categories"] == ["apm", "database", "host"]
    assert all(item["status"] == "CONFIGURED" for item in status["sources"])


def test_observability_http_json_connector_uses_environment_without_persisting_headers(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTOTEST_APM_URL", "https://monitor.example/api/performance?token=secret")
    monkeypatch.setenv("AUTOTEST_APM_HEADERS", '{"Authorization":"Bearer private"}')

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            return b'{"data":{"error_rate":2.5,"p95_ms":900}}'

    captured = {}

    def fake_urlopen(request, timeout=5):
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("quality_hub_backend.services.performance_observability.urllib.request.urlopen", fake_urlopen)
    evidence = collect_observability_evidence(
        tmp_path,
        manifest={
            "performance_observability": [{
                "type": "http_json",
                "category": "apm",
                "url_env": "AUTOTEST_APM_URL",
                "headers_env": "AUTOTEST_APM_HEADERS",
                "payload_path": "data",
            }]
        },
    )

    assert evidence["categories"]["apm"]["error_rate"] == 2.5
    assert evidence["sources"][0]["endpoint"] == "https://monitor.example/api/performance"
    assert "secret" not in str(evidence)
    assert "private" not in str(evidence)
    assert captured["headers"]["Authorization"] == "Bearer private"
    assert evidence["signals"][0]["signal"] == "application_errors"
