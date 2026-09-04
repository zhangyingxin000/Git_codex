from __future__ import annotations

import csv
import json
import os
import sqlite3
import threading
import urllib.request
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = ROOT / "requirements" / "demo" / "salary-trade"
ACCOUNT_CSV = DEMO_ROOT / "data" / "accounts.csv"
REPLAY_FILE = DEMO_ROOT / "replay" / "scenarios.json"
DATABASE_FILE = DEMO_ROOT / "seed.sqlite"
REPORT_ROOT = DEMO_ROOT / "reports"
RUNTIME_DATABASE_FILE = REPORT_ROOT / "latest" / "runtime.sqlite"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _read_accounts() -> list[dict[str, str]]:
    with ACCOUNT_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_scenarios() -> list[dict[str, Any]]:
    return list(json.loads(REPLAY_FILE.read_text(encoding="utf-8"))["scenarios"])


def seed_database(path: Path = DATABASE_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            CREATE TABLE demo_account (
                uid INTEGER PRIMARY KEY,
                role TEXT NOT NULL,
                country_code TEXT NOT NULL,
                currency TEXT NOT NULL,
                ticket TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE anchor_salary_trade_agent_whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid INTEGER NOT NULL,
                country_code TEXT NOT NULL,
                support_currencies TEXT NOT NULL,
                status INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE anchor_salary_trade_order (
                order_no TEXT PRIMARY KEY,
                scenario_id TEXT NOT NULL,
                applicant_uid INTEGER NOT NULL,
                agent_uid INTEGER NOT NULL,
                currency TEXT NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE anchor_salary_trade_order_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE anchor_salary_trade_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT NOT NULL,
                evidence_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        accounts = _read_accounts()
        connection.executemany(
            "INSERT INTO demo_account(uid, role, country_code, currency, ticket) VALUES(?,?,?,?,?)",
            [
                (int(row["uid"]), row["role"], row["country_code"], row["currency"], row["ticket"])
                for row in accounts
            ],
        )
        connection.executemany(
            "INSERT INTO anchor_salary_trade_agent_whitelist(uid, country_code, support_currencies) VALUES(?,?,?)",
            [
                (int(row["uid"]), row["country_code"], row["currency"])
                for row in accounts
                if row["role"] == "proxy"
            ],
        )
        connection.commit()
    finally:
        connection.close()
    return path


def _find_proxy(connection: sqlite3.Connection, country_code: str, currency: str) -> int:
    row = connection.execute(
        """
        SELECT uid
        FROM anchor_salary_trade_agent_whitelist
        WHERE status = 1
          AND country_code = ?
          AND instr(',' || support_currencies || ',', ',' || ? || ',') > 0
        ORDER BY id
        LIMIT 1
        """,
        (country_code, currency),
    ).fetchone()
    if not row:
        raise ValueError(f"No demo proxy matches {country_code}/{currency}")
    return int(row[0])


class DemoState:
    def __init__(self, database: Path) -> None:
        self.database = database
        self.lock = threading.Lock()

    def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.lock, sqlite3.connect(self.database) as connection:
            applicant = connection.execute(
                "SELECT uid, country_code, currency FROM demo_account WHERE uid=? AND role='applicant' AND active=1",
                (int(payload["applicant_uid"]),),
            ).fetchone()
            if not applicant:
                raise ValueError("Demo applicant is unavailable")
            processing = connection.execute(
                "SELECT 1 FROM anchor_salary_trade_order WHERE applicant_uid=? AND status NOT IN ('COMPLETED','CANCELLED','REJECTED')",
                (int(applicant[0]),),
            ).fetchone()
            if processing:
                raise ValueError("Applicant already has a processing order")
            proxy_uid = _find_proxy(connection, applicant[1], applicant[2])
            order_no = f"DEMO-{payload['scenario_id']}-{applicant[0]}"
            connection.execute(
                "INSERT INTO anchor_salary_trade_order VALUES(?,?,?,?,?,?,?,?)",
                (order_no, payload["scenario_id"], applicant[0], proxy_uid, applicant[2], 100, "CREATED", _now()),
            )
            connection.execute(
                "INSERT INTO anchor_salary_trade_order_log(order_no, action, status, created_at) VALUES(?,?,?,?)",
                (order_no, "create", "CREATED", _now()),
            )
            return {"order_no": order_no, "proxy_uid": proxy_uid, "status": "CREATED"}

    def apply_action(self, order_no: str, action: str, target_status: str) -> dict[str, Any]:
        with self.lock, sqlite3.connect(self.database) as connection:
            exists = connection.execute(
                "SELECT 1 FROM anchor_salary_trade_order WHERE order_no=?", (order_no,)
            ).fetchone()
            if not exists:
                raise ValueError("Demo order does not exist")
            connection.execute(
                "UPDATE anchor_salary_trade_order SET status=? WHERE order_no=?",
                (target_status, order_no),
            )
            connection.execute(
                "INSERT INTO anchor_salary_trade_order_log(order_no, action, status, created_at) VALUES(?,?,?,?)",
                (order_no, action, target_status, _now()),
            )
            if action.startswith("appeal_"):
                connection.execute(
                    "INSERT INTO anchor_salary_trade_evidence(order_no, evidence_type, content, created_at) VALUES(?,?,?,?)",
                    (order_no, action, "synthetic demo evidence", _now()),
                )
            return {"order_no": order_no, "status": target_status}


def _handler(state: DemoState):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size) or b"{}")
            try:
                if self.path == "/salary/trade/order/create":
                    result = state.create_order(payload)
                elif self.path == "/salary/trade/order/action":
                    result = state.apply_action(payload["order_no"], payload["action"], payload["target_status"])
                else:
                    self.send_error(404)
                    return
                body = json.dumps({"code": 200, "data": result}).encode("utf-8")
                self.send_response(200)
            except (KeyError, TypeError, ValueError) as exc:
                body = json.dumps({"code": 400, "message": str(exc)}).encode("utf-8")
                self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    return Handler


def _post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def run_demo() -> dict[str, Any]:
    os.environ["AUTOTEST_DEMO_MODE"] = "true"
    os.environ["AUTOTEST_ALLOW_MUTATIONS"] = "false"
    os.environ["AUTOTEST_ALLOW_HIGH_RISK"] = "false"
    os.environ["AUTOTEST_ALLOWED_HOSTS"] = "127.0.0.1,localhost"
    RUNTIME_DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    seed_database(RUNTIME_DATABASE_FILE)
    state = DemoState(RUNTIME_DATABASE_FILE)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    results = []
    try:
        for scenario in _read_scenarios():
            created = _post(
                base_url + "/salary/trade/order/create",
                {"scenario_id": scenario["id"], "applicant_uid": scenario["applicant_uid"]},
            )["data"]
            current = created
            for action in scenario["actions"]:
                current = _post(
                    base_url + "/salary/trade/order/action",
                    {
                        "order_no": created["order_no"],
                        "action": action["name"],
                        "target_status": action["status"],
                    },
                )["data"]
            results.append(
                {
                    "scenario_id": scenario["id"],
                    "name": scenario["name"],
                    "applicant_uid": scenario["applicant_uid"],
                    "proxy_uid": created["proxy_uid"],
                    "order_no": created["order_no"],
                    "expected_status": scenario["expected_status"],
                    "actual_status": current["status"],
                    "status": "PASSED" if current["status"] == scenario["expected_status"] else "FAILED",
                }
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    passed = sum(item["status"] == "PASSED" for item in results)
    report = {
        "report_type": "SALARY_TRADE_OFFLINE_DEMO",
        "schema_version": "1.0",
        "demo_mode": True,
        "external_writes": False,
        "generated_at": _now(),
        "status": "PASSED" if passed == len(results) else "FAILED",
        "summary": {"scenarios": len(results), "passed": passed, "failed": len(results) - passed},
        "artifacts": {
            "database_seed": str(DATABASE_FILE),
            "database_runtime": str(RUNTIME_DATABASE_FILE),
            "accounts": str(ACCOUNT_CSV),
            "replay": str(REPLAY_FILE),
        },
        "scenarios": results,
    }
    latest = REPORT_ROOT / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    report_path = latest / "demo-summary.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["report_path"] = str(report_path)
    return report


def main() -> int:
    report = run_demo()
    print("DEMO MODE: external writes are disabled; only localhost and synthetic SQLite data were used.")
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"Report: {report['report_path']}")
    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
