# Salary Trade Offline Demo

This package demonstrates the multi-account salary-trade workflow without using real
credentials or calling an external environment.

- `data/accounts.csv`: eight synthetic applicants and reusable proxies.
- `openapi.json`: minimal API contract used by the localhost mock service.
- `replay/scenarios.json`: eight ordered business flows and expected final states.
- `seed.sqlite`: immutable synthetic seed shipped with the repository.
- `reports/latest/runtime.sqlite`: disposable execution database regenerated before each run.
- `reports/latest/demo-summary.json`: latest unified scenario result.

Run from the repository root:

```powershell
.\platform.cmd demo
```

Demo mode forcibly sets mutation and high-risk switches to `false`, restricts hosts to
`127.0.0.1,localhost`, starts a temporary local service, executes all scenarios, writes
SQLite evidence, produces a report, and shuts the service down.
