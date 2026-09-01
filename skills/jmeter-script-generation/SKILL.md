# JMeter Script Generation Skill

## Purpose

Generate enterprise-recognized Apache JMeter plans from requirement packages and test cases. The workbench is only the orchestration hub; JMeter remains the execution and maintenance tool.

## Input Contract

Each generated script must be traceable to one requirement package and one test scenario. Required input fields:

- requirement_package_id
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

- smoke: 1 thread, 1 loop, low risk, used for connectivity and authentication.
- baseline: configurable threads and loops, used for stable baseline metrics.
- step_load: multiple stages with increasing threads, used to observe capacity changes.
- stability: longer duration with fixed target concurrency, used to observe error rate and tail latency.

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

Generated GUI plans should include:

- View Results Tree
- Summary Report
- Aggregate Report
- Graph Results or response-time graph listener
- Simple Data Writer to JTL

Generated non-GUI plans should include:

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
