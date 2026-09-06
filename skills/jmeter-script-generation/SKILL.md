---
name: jmeter-script-generation
description: Generate Apache JMeter plans from requirement packages, test cases, account models, YAML configuration, and runtime data rules.
metadata:
  short-description: Requirement package JMeter script generation
---

# JMeter Script Generation Skill

## Purpose

Generate enterprise-recognized Apache JMeter plans from requirement packages and test cases. The workbench is only the orchestration hub; JMeter remains the execution and maintenance tool.

## Generation Engine

Use the Skill as both the decision and constrained JMX generation layer. The Skill may use the installed `jmeter-generator` implementation or the platform template engine, but it must obey this contract before any MCP call.

- The Skill parses requirement cases, OpenAPI and the selected performance Profile, then produces the canonical `jmeter-plan.jmx`.
- The deterministic gate validates the generated or maintained JMX and may perform one format-only correction pass. It must never change thread groups, requests, assertions, load settings or business order.
- `mcp` is the single non-GUI execution gateway. It imports an approved JMX, executes it, generates JTL/HTML artifacts and returns execution metadata. It does not construct business samplers or rewrite the plan.
- Record the generation Skill, gate report, original/corrected hashes, MCP package version and execution workflow in the generated manifest.
- Credentialed plans use declared account CSV files or an ephemeral runtime CSV. Never persist raw uid/ticket/token values in JMX, JTL, HTML, MCP workspace metadata or platform reports.
- The platform owns requirement parsing, preflight, report retention, performance baselines, evidence recovery, threshold decisions and AI review; MCP owns JMX import, execution and artifact collection only.

## Execution Modes

JMeter is one execution engine with two strictly separated testing purposes.

### Business Scenario Mode

Use `jmeter_scenario` for complex requirement scenarios involving ordered API calls, multiple roles/accounts, extracted variables, state transitions, retries, branches and long business chains.

- The primary result is scenario correctness, not capacity.
- Assertions focus on step order, business status, role ownership, variable continuity and DB/Redis evidence.
- Use one thread per account slot unless the scenario explicitly tests concurrent business behavior.
- Output to `outputs/jmeter/scenario/` and archive reports under the scenario report category.

### Performance Mode

Use `jmeter_performance` only when the test objective is performance or capacity:

- `baseline`: one user or one thread, stable repetitions, establishes response-time and throughput baseline.
- `load`: gradually increases concurrency/load, finds the maximum load that still satisfies thresholds.
- `spike`: applies a rapid load increase and observes degradation and recovery.
- `soak`: normal target load for a long duration, from hours to days/weeks, observes error rate, tail latency and resource degradation.
- `concurrency`: simultaneous requests or users, validates contention, locks, duplicate writes and capacity behavior.
- `stress`: continues beyond expected capacity, identifies the failure point, degradation pattern and recovery behavior.

Performance reports must include response time, P50/P90/P95/P99, TPS/QPS or throughput, concurrent users, error rate, response codes, load stage, threshold result and the capacity inflection point when available. Output to `outputs/jmeter/performance/` and archive reports under the performance report category.

Never put business-scenario correctness and performance conclusions into the same JMX thread group or the same report conclusion. The same API chain may be used as a workload model, but it must be copied into a separate performance plan with an explicit profile.

## Input Contract

Each generated script must be traceable to one requirement package and one test scenario. Required input fields:

- requirement_package_id
- account_model.yaml
- case_id
- case_title
- business_flow
- role_context
- account_slots
- request_method
- request_path
- query_params
- headers
- body
- extract_rules
- assertions
- data_evidence_rules
- performance_profile

## Account Model First

Every JMeter generation run must load the selected requirement package's `account_model.yaml` before deciding script structure. Test cases describe what to verify; the account model decides how identities are supplied and isolated at runtime.

Required behavior:

- `single_account` packages must not receive CSV Data Set Config unless the selected test cases require data-driven execution.
- `dual_role` packages must generate separate role variables, for example applicant and proxy, and must validate that each ticket belongs to the matching uid.
- `multi_flow_slots` packages must generate flow slot variables so one workflow cannot accidentally reuse another workflow's applicant or order number.
- role credential sources must follow the model order: runtime parameters, CSV, login API, Redis readonly token cache, then block.
- DB tables from the model may provide candidate users and evidence only; DB must not be treated as a ticket source.
- unknown roles or unsupported matching rules must be written to the manifest as pending extensions instead of silently guessing.

The manifest must include the loaded account model path, mode, roles, credential sources, matching rules and blocking rules.

## YAML And CSV Boundary

YAML owns stable platform configuration only:

- environment name and base URL
- JMeter/Newman/tool paths
- readonly MySQL and Redis connection metadata
- feature switches, retry count and timeout
- report roots and metadata file paths
- paths to CSV execution data files

Test cases decide the runtime data carrier. CSV owns runtime script data only when the scenario needs data-driven execution:

- role rows such as applicant, proxy, operator and wealth_user
- uid, shortId and login source columns
- countryCode, currency and supportCurrencies
- scenario slot assignment
- per-run amount, page size, loop and data variation values

Single-account and single-flow scenarios may use runtime parameters, encrypted local credentials, login setup samplers, or Redis readonly token lookup without a CSV file.

Never put real passwords, long-lived tickets or production secrets in YAML. If a token must be reused locally, keep it in runtime properties, encrypted local credentials, Redis lookup, or an explicit CSV file that is excluded from public delivery.

## Thread Group Standards

Generate independent thread groups by requirement flow. Do not mix unrelated requirements in the same thread group.

- scenario_smoke: 1 thread, 1 loop, used only to prove a complex business flow can execute correctly.
- baseline: 1 user/thread with stable repetitions, used to establish single-user metrics.
- load: multiple stages with increasing users/threads, used to find the threshold-compliant maximum load.
- spike: rapid increase and decrease, used to observe burst handling and recovery.
- soak: long duration with normal target load, used to observe error rate, resource leakage and tail-latency drift.
- concurrency: synchronized users/requests, used to observe contention, locking and duplicate processing.
- stress: load beyond expected capacity, used to locate failure and recovery points.

Each thread group must include:

- clear business name
- role/account slot name
- concurrency
- ramp-up
- loop count or duration
- stop-on-error policy for strict workflow tests
- report label prefix containing requirement and case code

## CSV Parameterization

Use CSV Data Set Config for multi-account and multi-role scenarios.

Rules:

- do not add CSV Data Set Config to every script by default.
- applicant, proxy, operator and wealth_user must be separated by a `role` column or by separate CSV files.
- each scenario must use its own account slot, for example `flow_code`, `applicant_slot` and `proxy_slot`.
- one applicant can have only one processing salary order at a time.
- token values are runtime secrets and must not be written into public reports.
- when login is available, prefer login setup thread groups to refresh tokens.
- when Redis token reuse is configured, read token as readonly evidence only.
- generated JMX files must point to CSV paths from YAML and must not embed fixed local account values unless the user explicitly asks for a one-off debug script.

## Request Generation

For every HTTP sampler:

- put protocol, host and common mobile parameters in reusable defaults.
- keep JMeter variables unencoded, for example `${ticket}` not `%24%7Bticket%7D`.
- never append accidental method text into query values, for example `USDGET`.
- POST form requests must use `application/x-www-form-urlencoded` when the capture shows form body.
- JSON requests must use raw JSON body and `application/json`.

## Variable Extraction

Use extraction rules after the sampler that creates the value.

Recommended extractors:

- JSON Extractor for stable JSON fields.
- JSR223 PostProcessor for strict type checks and fallback parsing.
- Regular Expression Extractor only when the response is not JSON.

Common variables:

- access_token -> ticket
- uid -> role-specific uid
- orderNo -> scenario order number
- status -> current order status
- amount fields -> balance and settlement validation

## Assertions

Each sampler must have at least:

- HTTP status assertion
- business code assertion
- required field assertion

Workflow samplers must also have:

- state transition assertion
- role permission assertion
- idempotency or duplicate operation assertion when applicable
- data evidence assertion when DB/Redis metadata exists

## Listeners And Reports

Debug-only GUI plans may include:

- View Results Tree
- Summary Report
- Aggregate Report
- Graph Results or response-time graph listener
- Simple Data Writer to JTL

Generated non-GUI plans must disable heavy GUI listeners and include:

- JTL output path
- HTML report generation path
- statistics.json recovery
- label-to-case mapping manifest

## Performance Metrics

Every JMeter execution report must recover:

- samples
- success count
- error count
- error rate
- average response time
- min/max
- P50/P90/P95/P99
- throughput
- slowest sampler labels
- response code distribution

AI replay analysis must judge the result by SLA or configured threshold, not by visual charts alone.

## Baseline Contract

- Every run context contains separate `performance.baseline` and `performance.comparison` states.
- The first eligible result is `candidate`, never automatically `active`.
- Only a manually approved run becomes an `active` baseline and receives report-retention protection.
- Comparisons require the same environment, Profile and target fingerprint.
- Comparison outcomes are `not_compared`, `pass`, `improved` or `regressed`.
- AI analysis must include the baseline comparison and must not claim an application, DB, cache or network root cause from JTL alone.

## DB And Redis Evidence

DB and Redis are readonly evidence sources. JMeter may use generated variables from DB/Redis lookup, but it must not write to DB or Redis.

Allowed use:

- read account candidate metadata
- read token cache when configured
- read order status after interface execution
- read evidence and order logs

Forbidden use:

- update business tables
- delete Redis keys
- overwrite cached tokens
- create production-like data outside controlled test interfaces

## Output Contract

Each generation must produce:

- `.jmx` plan
- manifest JSON
- readable markdown summary
- launcher command or script
- expected runtime parameters
- report archive location

The manifest must include requirement package, cases, thread groups, samplers, extractors, assertions, listeners, performance profile and known blockers.
