---
name: pytest-evidence-review
description: Generate or improve pytest deep evidence review assets for requirement packages, using scenario plans, runtime variable extraction, HTTP results, DB/Redis evidence rules, and human-readable JSON reports.
metadata:
  short-description: Generate pytest deep evidence review from requirement scenarios
---

# pytest Evidence Review Skill

## Purpose

Generate a portable pytest review layer for a requirement package.

pytest is not the main state-machine runner. Newman is still good for lightweight API regression, and JMeter is still better for complex workflow execution and performance. pytest owns the post-execution review layer:

- run or replay HTTP checks when needed
- read JMeter JTL and Newman JSON when provided
- extract runtime variables from API responses
- query DB/Redis evidence rules
- output a structured JSON report for AI review and human maintenance

## General Model

Do not hard-code one business requirement into the pytest runner.

Use this abstraction:

```text
requirement package
-> manifest orchestration entry
-> scenario execution plan or future orchestration asset
-> ordered test cases
-> runtime variables
-> HTTP results
-> evidence_rules.yaml
-> DB/Redis read checks
-> pytest evidence JSON
```

Salary trade is only a reference sample because it has useful complexity: multiple roles, multiple scenarios, order state transitions, runtime identifiers, DB evidence, Redis login/cache evidence, and manual timing flows. Future requirements may have more roles, more scenarios, or different business identifiers, so generated pytest must stay driven by package-local rules and data.

## Inputs

Prefer package-local assets:

- `manifest.json` for package identity and the current orchestration entry
- the manifest `orchestration.primary_plan` file for scenario grouping and human review context; default to `outputs/execution-plan.json`
- `outputs/structured-test-cases.json` for case definitions and quality status
- `evidence_rules.yaml` for DB/Redis checks
- `account_model.yaml` for roles, credential sources, and blocking rules
- optional `runtime_aliases.yaml` for project-specific variable aliases
- optional JMeter JTL path and Newman JSON path from runtime environment

If a formal orchestration asset is missing, degrade gracefully to case `scenario_type` grouping and explain the fallback in the pytest evidence report instead of silently inventing fields. Do not treat `outputs/execution-plan.json` as a permanent global priority; it is the default package orchestration asset until the package manifest points to a more specific one.

## Runtime Variable Rules

The runner should maintain a runtime state while executing cases.

For scenario-driven execution, reset temporary runtime state at the start of each scenario while preserving environment-level values such as base URL, credentials, device context, and explicit runtime JSON. Identifiers produced inside one scenario, such as `orderNo`, `flowId`, or status values, must not leak into the next scenario unless the orchestration asset explicitly declares shared variables.

Variables can come from:

- explicit environment variables
- runtime JSON passed by the platform
- previous HTTP responses
- scenario execution plan data
- account model data
- package-local alias rules

Extract common scalar identifiers from JSON responses. Examples include:

- `id`, `orderId`, `orderNo`, `tradeNo`, `flowId`
- `uid`, `userId`, `agentUid`, `proxyUid`, `operatorId`
- `countryCode`, `currency`, `status`

Normalize common variants to both snake_case and camelCase where useful. For example, `orderNo` may populate `orderNo` and `order_no`.

When the next request has a query/body placeholder or an empty required parameter, fill it from runtime state. Do not write secrets into generated source files; inject tokens and passwords only at runtime.

For new business identifiers, add package-local `runtime_aliases.yaml`. Do not expand global code for a one-off field until it appears in multiple packages.

## Evidence Rules

`evidence_rules.yaml` is the stable contract between test cases and DB/Redis.

Rules should identify:

- data source: `mysql` or `redis`
- target table/key
- where/key expression using `${runtime_variable}`
- assertions over returned rows or values

The pytest runner must:

- allow only read-only SQL operations
- prefer scenario-bound evidence rule ids from the orchestration asset
- treat missing runtime variables as `BLOCKED`
- treat no returned records as `FAILED`
- treat assertion mismatch as `FAILED`
- preserve query location, assertion details, blockers, and small samples in JSON

Redis evidence is optional unless a requirement explicitly depends on login state, cache state, locks, rate limits, idempotency, or processing-state cache.

## Report Contract

Write a JSON report under `requirements/<package_id>/reports/pytest-evidence-*`.

The report should include:

- `report_type`
- `package_id`
- status: `PASSED`, `FAILED`, or `BLOCKED`
- summary counts for HTTP, DB/Redis rules, JMeter, and Newman
- redacted runtime variables
- HTTP result list with response preview
- JMeter summary when a JTL path is supplied
- Newman summary when a JSON report is supplied
- evidence rule results with queries, rows, assertions, blockers, and samples

Always redact tickets, tokens, passwords, and JWT-looking values.

## Maintenance Principle

The generated pytest should make human review easier, not harder.

Keep reports grouped by requirement package and scenario. A tester should be able to answer:

- which scenario failed
- whether the failure is HTTP, runtime data, DB/Redis evidence, or environment
- which input asset should be maintained next

When a complex business rule cannot be automated yet, emit a clear blocker and keep the scenario in the manual review path.
