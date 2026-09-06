import app


def test_jmeter_version_ignores_startup_warnings(monkeypatch):
    class Result:
        stdout = """
WARN StatusConsoleListener package scanning is deprecated
   APACHE JMETER 5.6.3
"""
        stderr = ""

    monkeypatch.setattr(app.subprocess, "run", lambda *args, **kwargs: Result())

    assert app._tool_version("C:/tools/jmeter.bat", ["--version"]) == "Apache JMeter 5.6.3"


def test_toolchain_high_risk_endpoints_are_warning_not_preflight_blocker(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "row", lambda *_: {"id": "project-1", "base_url": "https://test.example.com"})

    def fake_rows(sql, _params):
        if "FROM api_endpoints" in sql:
            return [{"risk_level": "high", "danger_score": 80}]
        if "FROM test_cases" in sql:
            return [{"id": "case-1"}]
        return []

    monkeypatch.setattr(app, "rows", fake_rows)
    monkeypatch.setattr(app, "_cached_toolchain_probes", lambda: [{"name": "pytest", "status": "READY"}])
    monkeypatch.setattr(app, "TOOL_ASSET_ROOT", tmp_path)

    result = app.enterprise_toolchain_status("project-1")

    assert result["status"] == "READY_WITH_WARNINGS"
    assert result["blockers"] == []
    assert result["warnings"] == ["1 个高风险接口在执行前需人工确认策略"]


def test_jmeter_mcp_probe_reports_gateway_blockers(monkeypatch):
    monkeypatch.setattr(
        app,
        "_jmeter_mcp_settings",
        lambda: {"node": "node", "bridge": "tools/jmeter-mcp/bridge.mjs", "blockers": ["MCP dependency missing"]},
    )

    result = app._jmeter_mcp_probe()

    assert result["name"] == "JMeter MCP"
    assert result["status"] == "MISSING"
    assert result["install_hint"] == "MCP dependency missing"
