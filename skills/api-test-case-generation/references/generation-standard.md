# Interface Test Case Generation Standard v2.0

## Coverage Weights

The complete case set must allocate coverage weight as follows:

- Normal: 40%. Required fields present, typical business data, successful protocol and business result.
- Exception: 40%. Authentication failure, missing/wrong parameter, missing resource, business conflict, and the mandatory exception library.
- Boundary: 20%. Minimum/maximum, empty, oversized, special characters and type boundaries.

The ratio is a weight contract, not permission to remove mandatory exception cases. Divide each bucket's fixed weight across the cases in that bucket and report both case counts and weight totals.

## Data Construction

| Field | Rule |
| --- | --- |
| Phone | `1` + a valid mobile prefix in the configured 300-399 range + seven random digits; use `{{random_phone}}`. |
| Identity card | Generate a value that passes GB 11643 checksum validation. |
| UUID | UUID v4, use `{{random_uuid}}`. |
| Amount | Two decimal places. Where item amounts exist, assert total equals their sum. |
| Time | ISO 8601 UTC, use `{{now_iso}}`. |
| Enum | Select only from documented `allowed_values`, using `{{random_enum(array)}}`. |
| Email | RFC 5322-compatible practical address, use `{{random_email}}`. |
| Text | Mixed Chinese/English text with spaces and punctuation; do not default to numeric-only or English-only filler. |
| Date | Business-valid dates for normal cases; invalid format/empty for negatives; 1970-01-01 and 2038-01-19 for boundaries. |
| Boolean | Test both `true` and `false`; negatives include string `"true"` and numeric `1`. |

When a string lacks length constraints, infer `1..255` and mark the affected case and field metadata with `inferred: true` and `inference_source: default_string_length`.

## Assertion Layers

Apply all applicable layers in order:

1. Protocol: HTTP/gRPC/WebSocket status or close code.
2. Structure: response Schema, required fields, types, formats, headers, arrays and pagination totals.
3. Business: every documented business expression, ownership rule, amount relation and state constraint.
4. Data: execute only supplied `sql_check` or approved metadata-backed rules. Otherwise mark skipped.
5. Per-request SLA: response time less than the configured threshold, default 500 ms.

Do not treat the 500 ms assertion as baseline/load/stability capacity evidence.

## Mandatory Exception Library

Generate applicable cases for every interface:

| Scenario | Operation | Expected behavior |
| --- | --- | --- |
| Empty payload | Empty body/parameters | 400 or explicit missing-parameter error. |
| Maximum capacity | Put a 1 MB random string in one eligible field | 413, explicit size rejection, or documented truncation warning. |
| Unicode attack | Include `\u0000` | Reject or safely handle without storage corruption. |
| Type confusion | Send numeric/boolean values as strings and vice versa | Explicit type error. |
| SQL injection | Include `' OR '1'='1` | Escape/reject; no extra data or SQL error leakage. |
| XSS | Include `<script>alert(1)</script>` | Escape or reject; never execute or persist unsafely. |
| Path traversal | Include `../` in an eligible path/string field | 403 or explicit rejection; no filesystem disclosure. |
| Duplicate submission | Repeat the same idempotency key/request | 409 or documented idempotent result; no duplicate side effects. |
| Oversized ID | Integer `999999999999999999999` | Range error without 500. |
| Negative amount | Amount `-100.00` | Business validation error without mutation. |
| Timeout simulation | Use a documented delay/fault parameter | 504 or documented timeout behavior. Skip and mark not applicable when unsupported. |

Deterministically mark 20% of cases with an exploratory unknown field such as `__debug: true`. For arrays, add order variation when order is not documented as significant.

Security, 1 MB, timeout, duplicate mutation, and concurrency cases require isolated-test authorization before execution.

## Protocol Detection

- REST: OpenAPI/Swagger, `/api/`, or HTTP methods. Validate method, route, path/query/header/body and HTTP response.
- gRPC: `.proto`, `service`, or RPC methods. Validate `grpc-status`, message schema and metadata; do not use HTTP status as the business assertion.
- GraphQL: schema, `query {` or `mutation {`. Validate `errors`, requested fields, nullability and nesting depth.
- WebSocket: `ws://`, `wss://` or upgrade headers. Validate message order, sequence IDs, Ping/Pong, reconnect and close codes.
- File stream: `application/octet-stream`. Validate size, checksum/MD5 when declared, range/chunk integrity and filename/content headers.
- Message queue: topic/queue, producer/consumer, or message-schema definitions. Validate publish acknowledgement, key, headers, ordering when declared, retry/dead-letter behavior, and consumption evidence.

## Dependencies And Callbacks

- Store dependency extraction in `context.dependencies` with source, JSON/path expression and `store_as`.
- Define every placeholder used by payload or assertions in `context.variables`.
- Mark circular dependencies explicitly and recommend a Mock boundary.
- For third-party callbacks, generate a Mock Expectation containing expected method, path, headers, payload schema, response and timeout. Do not call the real third party.

## Priority

When more than ten interfaces are present, generate and review core CRUD and authentication interfaces first, then auxiliary queries, callbacks and maintenance endpoints. The final full output may contain all interfaces, but priority and generation batches must remain visible.

## Quality Gate

Before output, cover required fields, enums and all boundary points; include at least five exception types plus SQL injection, XSS, duplicate/idempotency and concurrency; resolve every variable and dependency; attach cleanup to every mutation case; include protocol, structure and business assertions; add per-request SLA assertions to at least 50% of cases; and validate JSON plus the case contract.

Repair a failing design once. If it still fails, return `quality_gate.status: FAILED` with findings instead of claiming compliance.
