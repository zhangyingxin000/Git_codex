# Interface Case Contract

## Case Meaning

A generated interface case is a reviewable test design, not proof that the scenario has run. Keep design status, automation mapping and execution result separate.

## Test Dimensions

| Dimension | Purpose |
| --- | --- |
| 功能 | Confirm the valid business path and response contract. |
| 响应契约 | Confirm HTTP status, business code, required response fields, types, enums and sensitive-field exposure. |
| 参数校验 | Confirm required, type, format and malformed request handling. |
| 等价类 | Represent valid and invalid input partitions without arbitrary duplication. |
| 边界值 | Verify values immediately below, at and above declared limits. |
| 认证授权 | Verify credentials, identity ownership and role permissions. |
| 异常处理 | Verify malformed payloads, explicit errors and absence of uncontrolled 500 responses. |
| 可靠性 | Verify duplicate submission, idempotency and consistent retry behavior. |
| 并发 | Verify uniqueness, locking and final data consistency under simultaneous actions. |
| 安全 | Verify hostile input is not interpreted, leaked or persisted unsafely. |

## Expected Result Quality

Do not use only “request failed” or “request succeeded”. Expected results should cover applicable layers:

- HTTP status range.
- Business code and message contract.
- Required response fields and types.
- Business state or ownership result.
- No unintended DB write or duplicate record.
- DB/Redis evidence when a formal rule exists.
- No stack trace, SQL error, secret or unrelated user data leakage.

## Missing Schema

When minimum, maximum, length, enum, pattern or format constraints are absent, do not manufacture them. Generate only defensible classes and add a design gap requesting the missing contract.
