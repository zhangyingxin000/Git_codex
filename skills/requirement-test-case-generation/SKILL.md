---
name: requirement-test-case-generation
description: Generate business requirement test cases from product requirements, workflows, rules, and acceptance criteria. Use for roles, state transitions, alternate and exception flows, account/data needs, and end-to-end business evidence; do not use for single-interface parameter enumeration or performance-capacity plans.
metadata:
  short-description: Business requirement test case design
---

# Requirement Test Case Generation

Generate reviewable business requirement cases before execution plans or tool scripts are created.

## Scope

- Input: requirement documents, acceptance criteria, process or state diagrams, business rules, UI descriptions, interface references, data dictionaries, and known defects.
- Output: business scenarios and requirement-level test cases in `outputs/structured-test-cases.*`.
- Cover roles, permissions, business objects, state transitions, alternate paths, failures, time conditions, compensation, consistency, auditability, and manual checkpoints.
- Exclude single-interface field permutations, protocol fuzzing, and formal baseline/load/stability/stress plans. Route those to the interface-test or performance-test design stage.

## Required Workflow

1. Extract requirement statements and assign stable requirement references.
2. Identify actors, permissions, business objects, states, transitions, invariants, time rules, external systems, and acceptance criteria.
3. Build the role model and state-transition graph before writing cases. Record unclear or contradictory rules as gaps instead of inventing them.
4. Design the main flow first, then alternate, exception, boundary, permission, timeout, compensation, idempotency, and recovery flows.
5. Use scenario analysis for workflows, state-transition testing for lifecycle rules, decision tables for condition combinations, and pairwise selection only when exhaustive combinations are impractical.
6. Determine account and data needs from the generated steps. Do not assume CSV, DB, Redis, Mock, or multiple accounts unless the requirement provides evidence.
7. Attach observable expected results at the UI/API, business, DB/cache/message, and audit-log levels when those sources are known.
8. Classify automation readiness without claiming an implementation exists. Keep manual-only and long-wait cases visible.
9. Run the quality gate, then write JSON, Markdown, and Excel using the same case IDs.
10. Generate account, evidence, resource-preflight, and execution-plan candidates only after cases stabilize.

Read [references/generation-standard.md](references/generation-standard.md) for coverage and design rules. Read [references/case-contract.md](references/case-contract.md) whenever generating or validating structured output. Machine-readable defaults are in `rules.yaml`.

## Non-Negotiable Rules

- Every important acceptance criterion must map to at least one case, and every case must map back to a requirement reference.
- One scenario owns one business objective and one coherent state path. Preserve the same business object identifier, such as `orderNo`, throughout that scenario.
- Separate independent scenarios when they require different initial data or when an actor cannot have two processing objects at once.
- Do not duplicate interface-level boundary and injection cases in requirement cases unless they change a business outcome or state.
- Do not present a 500 ms request assertion, concurrency count, or duration as a performance conclusion.
- Databases are business data and evidence sources, not authentication sources. Credentials must come from declared runtime values, account files, login APIs, or approved login-state sources.
- Missing information becomes a structured gap with impact, affected cases, and a suggested source. Never silently fill business enums, status transitions, identities, table names, Redis keys, or credentials.
- Reuse package-local `resource_manifest.yaml`, `account_model.yaml`, and official `evidence_rules.yaml`. Candidate output must not overwrite a maintained formal asset.
- Third-party callbacks use a Mock expectation unless the tester explicitly authorizes a test endpoint.
- Real writes, destructive cleanup, security probes, and long-duration waits remain blocked until the target environment and authorization pass preflight.

## Coverage Model

For every business capability, consider:

- Main success path and acceptance result.
- Alternate valid paths and optional branches.
- Business-rule conflicts and invalid state transitions.
- Role, ownership, tenant, and permission separation.
- Duplicate submission, retry, idempotency, interruption, and recovery.
- Timeout, expiration, scheduled processing, compensation, and eventual consistency.
- Minimum, maximum, empty, and threshold values only where they affect the business rule.
- Downstream failure, callback failure, message delay/duplication, DB/cache inconsistency, and audit logging when applicable.

Do not force irrelevant categories. Mark a category `NOT_APPLICABLE` with a reason when the requirement genuinely does not contain it.

## Asset Handoff

After the structured cases pass review:

- Ask `account-model-generation` to derive single-account, multi-role, multi-account, or data-matrix needs from the cases.
- Generate resource-preflight expectations from actual case dependencies and persist reusable source declarations in `resource_manifest.yaml`.
- Generate candidate evidence rules from expected business outcomes and known DB/Redis/message metadata. Keep uncertain rules as candidates.
- Generate an execution-plan candidate that groups cases by business scenario and selects tools without splitting the maintained requirement into separate products.
- Preserve traceability: `requirement_ref -> case_id -> scenario_id -> tool task -> evidence rule -> report result`.

The requirement package remains the maintenance unit even when Newman, JMeter, pytest, or manual verification perform different parts of the execution.
