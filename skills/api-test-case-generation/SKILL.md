---
name: api-test-case-generation
description: Generate interface-level test case designs from REST, gRPC, GraphQL, WebSocket, or file-stream API definitions. Use for protocol, parameter, schema, business-rule, data, and per-request SLA validation; do not use for end-to-end requirement scenarios or capacity/performance plans.
metadata:
  short-description: Strict interface test case design
---

# Interface Test Case Generation

Generate reviewable interface test cases before any Newman, pytest, JMeter, Apifox, or other execution script is created.

## Scope

- Input: API documentation, OpenAPI/Swagger/Apifox export, `.proto`, GraphQL schema/query, WebSocket contract, file-stream contract, captured examples, and optional business/data rules.
- Output: interface test case design only.
- Exclude: end-to-end requirement flows, multi-role state machines, load profiles, capacity conclusions, and long-duration performance plans.
- Keep interface cases in `outputs/api-test-cases/`; never overwrite `outputs/structured-test-cases.*`.

## Required Workflow

1. Detect the protocol from the input.
2. Extract fields, locations, types, required flags, formats, lengths, enums, examples, response schemas, business rules, dependencies, callbacks, and optional DB checks.
3. Build the dependency graph before generating cases. Mark cycles and recommend a Mock boundary.
4. Generate normal, exception, and boundary scenarios with coverage weights `40:40:20`.
5. Apply the deterministic data construction rules and record every inferred constraint.
6. Build all five assertion layers: protocol, structure, business, optional data, and per-request SLA.
7. Add cleanup for every create/mutation case.
8. Run the quality gate before writing JSON, Markdown, or Excel.
9. Only after review, compile cases into tool-specific scripts while preserving `case_id`.

Read [references/generation-standard.md](references/generation-standard.md) for coverage, data construction, mandatory exceptions, protocol recognition, and special handling. Read [references/case-contract.md](references/case-contract.md) whenever generating or validating the JSON output. Machine-readable defaults are in `rules.yaml`.

## Non-Negotiable Rules

- Every case must contain every field required by the case contract.
- The coverage summary must report normal/exception/boundary counts and weights. Weight totals must be exactly `40/40/20`; mandatory exception cases may be more numerous without changing their total 40% weight.
- Missing constraints may be inferred only from configured defaults and must set `inferred: true` with the inferred source recorded.
- Enum values must come from `allowed_values`/Schema. Never invent enums.
- Do not use only `code == 0` or HTTP 200 as the assertion.
- Validate response headers, required response fields/types/formats, array length or pagination totals when applicable.
- Security, 1MB payload, mutation, callback, concurrency, and timeout cases are design assets until the target test environment and authorization pass preflight.
- A 500 ms assertion is a per-request interface SLA default, not a performance-capacity conclusion. Formal baseline/load/stability/concurrency/stress testing belongs to the performance plan.
- If DB connection metadata or `sql_check` is absent, do not invent SQL. Mark the data assertion as skipped and request the test datasource once through the requirement package resource manifest.

## Execution Handoff

Compile reviewed cases by protocol and tool:

- REST normal/negative/ordinary boundaries: Newman or Apifox CLI.
- Deep business expressions, DB checks, security analysis, protocol adapters: pytest.
- WebSocket or gRPC specialized clients when available.
- Concurrency candidates: separate JMeter performance or scenario plans, never the ordinary interface report.

Before execution, resolve variables from dependency outputs, package CSV files, resource manifests, saved runtime parameters, and allowed data sources. Block unresolved variables instead of sending placeholder text. Write results back by `case_id` and keep interface, business-scenario, and performance reports separate.
