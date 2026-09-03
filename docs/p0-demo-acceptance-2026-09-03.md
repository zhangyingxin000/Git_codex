# P0 Demo Acceptance - 2026-09-03

## Scope

- Offline salary-trade demo package
- Eight-account batch execution
- Forced demo safety mode
- JMeter adapter import repair
- Reproducible dependency declaration

## Verification

| Check | Result |
| --- | --- |
| Focused P0 tests | 4 passed |
| Full platform regression | 25 passed |
| Python compile check | passed |
| Frontend JavaScript syntax | passed |
| Demo scenarios | 8 passed, 0 failed |
| Distinct applicants | 8 |
| Matched proxies | 3 |
| Created orders | 8 |
| Order log rows | 27 |
| External hosts contacted | 0 |

## Safety conclusion

The demo uses synthetic account identifiers and tickets, a localhost-only temporary HTTP
service, and a local SQLite database. It forcibly disables external mutation and high-risk
switches even when the parent environment previously enabled them.

## Reproduction

```powershell
.\platform.cmd setup
.\platform.cmd demo
.\platform.cmd check
```

The first command is needed only on a new machine. Normal demo runs use the single
`platform.cmd demo` command.
