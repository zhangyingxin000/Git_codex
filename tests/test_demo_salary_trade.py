import json
import os
import sqlite3

from quality_hub_backend.demo.salary_trade import DATABASE_FILE, REPORT_ROOT, run_demo


def test_salary_trade_demo_runs_eight_independent_accounts(monkeypatch) -> None:
    monkeypatch.setenv("AUTOTEST_ALLOW_MUTATIONS", "true")
    monkeypatch.setenv("AUTOTEST_ALLOWED_HOSTS", "example.invalid")

    report = run_demo()

    assert report["status"] == "PASSED"
    assert os.environ["AUTOTEST_ALLOW_MUTATIONS"] == "false"
    assert os.environ["AUTOTEST_ALLOW_HIGH_RISK"] == "false"
    assert os.environ["AUTOTEST_ALLOWED_HOSTS"] == "127.0.0.1,localhost"
    assert report["summary"] == {"scenarios": 8, "passed": 8, "failed": 0}
    assert len({item["applicant_uid"] for item in report["scenarios"]}) == 8
    assert len({item["order_no"] for item in report["scenarios"]}) == 8
    assert all(str(item["proxy_uid"]).startswith("920") for item in report["scenarios"])

    with sqlite3.connect(DATABASE_FILE) as connection:
        assert connection.execute("SELECT COUNT(*) FROM anchor_salary_trade_order").fetchone()[0] == 8
        assert connection.execute("SELECT COUNT(DISTINCT applicant_uid) FROM anchor_salary_trade_order").fetchone()[0] == 8
        assert connection.execute("SELECT COUNT(*) FROM anchor_salary_trade_order_log").fetchone()[0] > 8

    saved = json.loads((REPORT_ROOT / "latest" / "demo-summary.json").read_text(encoding="utf-8"))
    assert saved["demo_mode"] is True
    assert saved["external_writes"] is False
