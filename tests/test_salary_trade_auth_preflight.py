import app


def _case(path):
    return {
        "title": "正常请求",
        "method": "GET",
        "path": path,
        "headers": "{}",
        "payload": "",
        "expected_status": 200,
    }


def test_salary_trade_auth_preflight_checks_both_roles(monkeypatch):
    seen = []

    def fake_probe(project, cases, runtime, **kwargs):
        seen.append((cases[0]["path"], runtime["uid"], runtime["ticket"]))
        return {"status": "PASSED", "summary": "ok", "items": []}

    monkeypatch.setattr(app, "_readonly_auth_probe", fake_probe)
    result = app._salary_trade_auth_preflight(
        {"base_url": "https://example.test"},
        [
            _case("/userserv/salary/trade/quota"),
            _case("/userserv/salary/trade/agent/notice"),
        ],
        {
            "applicant_uid": "1001",
            "applicant_ticket": "applicant-token",
            "proxy_uid": "2001",
            "proxy_ticket": "proxy-token",
        },
    )

    assert result["status"] == "PASSED"
    assert seen == [
        ("/userserv/salary/trade/quota", "1001", "applicant-token"),
        ("/userserv/salary/trade/agent/notice", "2001", "proxy-token"),
    ]


def test_readonly_auth_probe_accepts_cases_before_runtime_placeholders(monkeypatch):
    monkeypatch.setattr(
        app.urllib.request,
        "urlopen",
        lambda request, timeout=15: type(
            "Response",
            (),
            {
                "status": 200,
                "read": lambda self, size: b'{"code":200,"message":"success"}',
            },
        )(),
    )
    result = app._readonly_auth_probe(
        {"base_url": "https://example.test"},
        [_case("/userserv/salary/trade/quota")],
        {"uid": "1001", "ticket": "ticket-value"},
    )

    assert result["status"] == "PASSED"


def test_salary_trade_auth_preflight_blocks_missing_proxy_ticket(monkeypatch):
    monkeypatch.setattr(
        app,
        "_readonly_auth_probe",
        lambda project, cases, runtime, **kwargs: {"status": "PASSED", "summary": "ok", "items": []},
    )
    result = app._salary_trade_auth_preflight(
        {"base_url": "https://example.test"},
        [_case("/userserv/salary/trade/quota")],
        {
            "applicant_uid": "1001",
            "applicant_ticket": "applicant-token",
            "proxy_uid": "2001",
            "proxy_ticket": "",
        },
    )

    assert result["status"] == "BLOCKED"
    assert "代理人" in result["message"]
