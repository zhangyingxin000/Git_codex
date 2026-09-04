---
name: api-test-case-generation
description: Generate traceable API test case designs from OpenAPI or captured interface schemas using equivalence partitioning, boundary value analysis, authentication, reliability, concurrency, and isolated security scenarios.
metadata:
  short-description: Schema-driven API test case design
---

# API Test Case Generation

Use this skill when a requirement package needs interface test cases generated or refreshed from OpenAPI, Swagger, Apifox export, HAR-derived schemas, or maintained API metadata.

## Scope Boundary

This Skill generates **interface test cases**, not requirement/business test cases.

- Interface test cases validate one API's request contract, response contract, equivalence partitions, boundaries, authentication, exception behavior, idempotency, concurrency and security behavior.
- Requirement test cases validate end-to-end business scenarios, state transitions, multiple roles/accounts, cross-interface sequencing and business evidence.
- Keep the outputs separate. Interface cases belong in `outputs/api-test-cases/`; requirement cases belong in `outputs/structured-test-cases.*`.
- Interface cases may be referenced by a business scenario, but must never replace or overwrite the requirement test case.

## Required Inputs

- The selected requirement package and its business requirement.
- The latest interface schema or captured request example.
- Parameter location, required flag, type, format, enum, pattern, minimum, maximum, minLength and maxLength when available.
- Authentication and role context from the package account model.
- Business assertions and DB/Redis evidence rules when the requirement defines them.

Do not invent constraints that are absent from both the schema and requirement. Missing constraints must be reported as design gaps.

## Generation Contract

Generate a valid baseline case for every operation, then derive field-level cases:

1. Required fields: missing value and empty/null boundaries where applicable.
2. Types: valid type and one invalid type class.
3. Enums: every declared valid value and one value outside the enum.
4. Numeric boundaries: `min-1`, `min`, `min+1`, `max-1`, `max`, `max+1` when limits exist.
5. Length boundaries: `minLength-1`, `minLength`, `minLength+1`, `maxLength-1`, `maxLength`, `maxLength+1`.
6. Formats and patterns: valid example when provided and invalid format/pattern input.
7. Authentication: missing, invalid, expired and role/UID mismatch when identity context supports them.
8. Mutation APIs: duplicate submission, idempotency and concurrent submission.
9. JSON bodies: malformed JSON and missing required body fields.
10. Security strings: SQL injection and XSS candidates, always marked for isolated test environments and human confirmation.
11. Protocol contract: unsupported HTTP method, missing required request body, mismatched Content-Type and malformed JSON.
12. Response contract: HTTP status, business code, required response fields, types, enums and sensitive-field leakage.

Read [references/case-contract.md](references/case-contract.md) when producing or reviewing the output structure. Machine-readable defaults are in `rules.yaml`.

## Tool Routing

- Newman or Apifox CLI: normal classes, required fields, types, enums, ordinary boundaries and authentication smoke cases.
- pytest: complex combinations, business assertions, authorization, idempotency, DB/Redis evidence and security result analysis.
- JMeter: concurrent submission, repeated requests and performance-related interface scenarios.

The same case may map to more than one tool, but keep one primary recommended tool and record secondary mappings separately.

## Safety

- SQL injection, XSS, path traversal, oversized payloads and destructive mutation cases must not run against production.
- Mark security and mutation-concurrency cases `REVIEW_REQUIRED` unless the selected environment explicitly permits them.
- Never include real passwords, tickets or tokens in generated public assets.
- A generated case is a design asset until its required data, identity, environment and assertions pass preflight.

## Required Output

Each case must contain:

- case ID and operation ID
- interface name, method and path
- test dimension and design technique
- valid/invalid equivalence partition
- field-level request mutation
- preconditions, steps and expected result
- priority, recommended tool and automation status
- security execution policy

Write package-local JSON, Markdown and Excel outputs. Include summary counts by interface, dimension, tool and review status. Every subsequent Newman, pytest or JMeter generation should consume or reference this case design instead of silently creating unrelated cases.
