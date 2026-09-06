# Interface Test Suite Contract v2.0

## Suite Root

Every JSON output contains `test_suite`, `cases`, `execution_order`, and `summary`. Multi-interface packages use `target.endpoint: multiple`; each case carries its method and endpoint in `meta`.

## Required Case Shape

```json
{
  "case_id": "TC_ORDER_001_normal",
  "description": "中文用例目的",
  "priority": "critical",
  "tags": ["smoke", "regression"],
  "meta": {
    "protocol": "rest",
    "method": "POST",
    "endpoint": "/api/orders",
    "scenario_type": "normal",
    "coverage_weight": 1.25,
    "inferred": false,
    "need_review": false
  },
  "context": {"dependencies": [], "variables": {}},
  "payload": {
    "path": {}, "query": {}, "headers": {}, "body": {},
    "mutation": {"action": "use_valid_baseline"}
  },
  "assertions": {
    "protocol": {"status": 200, "headers": ["Content-Type"]},
    "schema": {},
    "business_logic": [],
    "db_check": null,
    "cache_check": null,
    "message_check": null,
    "performance": {"max_response_ms": 500}
  },
  "cleanup": {"action": "none", "on_fail": "ignore", "retry": 0, "timeout": 5000}
}
```

All fields above are mandatory. Protocol-specific assertions may add `grpc_status`, `close_code`, `opcode`, `trailers`, `graphql_errors`, `content_length`, `checksum`, or message-consumption fields.

## Case IDs

Use `TC_{MODULE}_{NNN}_{scenario}`. Module uses uppercase ASCII letters, numbers and underscores; sequence is three digits from `001`; scenario is exactly `normal`, `exception`, or `boundary`. Security, concurrency and performance are tags, not suffixes.

## Inference

When a request value, constraint, status, cleanup action, assertion, or dependency is not documented, set `inferred: true`, `need_review: true`, and provide a suggestion. Propagate aggregate flags to `meta`.

## Variables

Every `{{variable}}` used by payload, assertions, cleanup, or dependencies must be defined by `context.variables`, an earlier dependency `store_as`, a requirement resource binding, or a documented built-in function. Unresolved placeholders fail the quality gate.

## Summary

Include total and scenario counts, weights exactly 40/40/20, protocol/interface counts, inferred/review counts, assertion depth, mutation cleanup coverage, performance assertion coverage, quality-gate findings, and estimated duration.
