# Demo Runbook

## Goal

Demonstrate the salary-trade multi-account orchestration and evidence loop on any Windows
machine without real credentials, network access, MySQL, Redis, or JMeter.

## Run

```powershell
cd <AutoTest-AI>
.\platform.cmd demo
```

The first run creates `.venv` when needed. Later runs reuse it.

## What happens

1. Demo mode forcibly disables external mutations and high-risk calls.
2. The outbound host allowlist is replaced with `127.0.0.1,localhost`.
3. The committed `seed.sqlite` remains unchanged and a fresh ignored runtime copy is created.
4. A temporary localhost HTTP service is started on a random free port.
5. Eight applicants execute eight independent order flows in scenario order.
6. Proxies are selected from the whitelist by applicant country and requested currency.
7. Orders, state logs, and complaint evidence are written only to the local demo SQLite file.
8. The service is stopped and a unified JSON report is written under the demo package.
9. Focused regression tests verify the demo, dependency contract, and JMeter adapter.

## Expected result

The command exits with code `0` and prints:

```text
DEMO MODE: external writes are disabled; only localhost and synthetic SQLite data were used.
{"scenarios": 8, "passed": 8, "failed": 0}
```

The generated report is `requirements/demo/salary-trade/reports/latest/demo-summary.json`.

## Safety evidence

- All account IDs and tickets in the package are synthetic.
- No production or test environment hostname is used.
- The default platform mutation and high-risk switches are both `false`.
- Demo mode overrides caller-provided unsafe environment values.
- Real reports, JTL files, `.env` files, and runtime account CSV files remain Git-ignored.
