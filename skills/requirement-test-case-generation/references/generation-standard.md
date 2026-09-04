# Requirement Case Generation Standard

## 1. Requirement Model

Extract these assets before generating cases:

- Requirement statements and acceptance criteria.
- Actors, roles, permissions, ownership, and tenant boundaries.
- Business objects and identifiers.
- Initial states, terminal states, legal transitions, forbidden transitions, and invariants.
- Time windows, expiration rules, scheduled tasks, retries, and compensation.
- External systems, callbacks, messages, databases, caches, and audit requirements.
- Known data restrictions, such as one applicant having only one processing order.

Unknown information must be added to `requirement_gaps`. Include why it matters, which scenarios it blocks, and what source could resolve it.

## 2. Scenario Construction

Create a scenario for one business objective and one coherent state path. A scenario can contain several test cases, but its business object ID must remain stable through the path.

Split scenarios when:

- The terminal outcome differs.
- The acting role or permission boundary differs.
- The initial state or required dataset differs.
- A user/account cannot safely execute both paths at the same time.
- Cleanup or compensation differs materially.

Do not split a maintained requirement package merely because different tools execute its cases.

## 3. Technique Selection

- Scenario analysis: end-to-end and alternate business flows.
- State transition: lifecycle and invalid-transition coverage.
- Decision table: combinations of permissions, flags, statuses, amounts, countries, currencies, or other conditions.
- Equivalence partition: business-valid and business-invalid categories.
- Boundary value: thresholds defined by the business, not every transport field.
- Pairwise: reduce large independent combinations while retaining interaction coverage.
- Error guessing: duplicate submission, interruption, retry, partial success, stale data, callback failure, and race conditions.

Record the selected technique on every case.

## 4. Account And Resource Decisions

Start with one account. Add roles when different actors perform different steps. Add account slots when scenarios must run independently or an account has a one-processing-object constraint. Add a data matrix only when combinations are an explicit coverage goal.

Infer resource types from concrete needs:

- CSV/file: tester-provided reusable identities or datasets.
- DB: candidate lookup, setup, business evidence, or cleanup.
- Redis/cache: login state or cache evidence only when declared.
- Login API: credential acquisition when account material supports it.
- Mock: third-party callback, unavailable dependency, or controlled failure injection.
- Message broker: publish/consume evidence when the requirement includes asynchronous processing.

Persist confirmed reusable declarations in the package resource manifest. Do not request the same resource again unless validation fails or its schema changes.

## 5. Expected Results And Evidence

Expected results must be observable and layered where applicable:

1. User or caller-visible result.
2. API/business response and error semantics.
3. Business state and invariant.
4. DB/cache/message evidence using known metadata.
5. Audit, notification, or downstream side effect.
6. Cleanup or compensation result.

Never invent SQL, tables, fields, Redis keys, topics, or business status values. Missing metadata produces an evidence candidate or gap.

## 6. Automation Classification

- `SCRIPT_GENERATION_READY`: steps, data, expected results, and required assets are available.
- `SCRIPTABLE_EVIDENCE_PENDING`: actions can be scripted but evidence rules need confirmation.
- `DATA_BLOCKED`: required account/data source is missing or invalid.
- `MANUAL_ONLY`: human judgment, external operation, or impractical wait is essential.
- `NOT_APPLICABLE`: a coverage category does not apply and has a recorded reason.

Automation readiness describes the case, not the existence of a finished script.

## 7. Quality Gate

Reject or mark the output for review when:

- An acceptance criterion has no case.
- A case lacks a requirement reference or expected result.
- A stateful scenario has no initial state, transition path, or terminal result.
- A write flow has no cleanup, rollback, compensation, or controlled-retention strategy.
- The same account is assigned to incompatible concurrent scenarios.
- Required resources are assumed but not declared.
- An official account model, evidence rule file, resource manifest, or execution plan would be overwritten.
