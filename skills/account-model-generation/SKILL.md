---
name: account-model-generation
description: Generate a per-requirement account model for API, JMeter, Newman, and pytest execution when a requirement may need single-user, multi-role, multi-account, or data-matrix test identities.
metadata:
  short-description: Requirement package account model generation
---

# Account Model Generation

Use this skill when a requirement package needs execution identities, credentials, role separation, account pools, or business matching rules.

The output is a package-local `account_model.yaml`. The common template defines available capabilities; the generated model enables only what the requirement and test cases justify.

## Decision Rule

Default to `single_account` unless there is evidence for a more complex model.

Upgrade to `dual_role` only when requirements, test steps, or API fields show two or more acting roles, such as applicant/proxy, payer/payee, anchor/audience, reviewer/operator, owner/member.

Upgrade to `multi_flow_slots` when cases must cover multiple independent business flows and an account cannot safely be reused across those flows, such as one user having only one processing order.

Use `data_matrix` only when the test purpose is explicitly to cover many combinations of level, country, currency, identity, permission, version, or channel.

Do not add roles, CSV files, DB tables, or Redis keys merely because they might be useful. Unknown signals become pending extensions for tester confirmation.

## Credential Sources

Resolve identity credentials in this order:

1. Runtime values explicitly passed by the tester.
2. Role CSV values such as `ticket`, `password_encrypted`, or `redis_uid`.
3. Login API using `shortId` and encrypted password.
4. Redis readonly cache, usually `user_login_info:{uid}.access_token`.
5. Block execution when no valid credential can be resolved.

Tokens must be checked against the role uid when the token format allows it. A token for a different uid is a blocking error.

## Data Source Boundary

Databases provide business candidates and evidence, not authentication. Redis may provide login cache or cache evidence. Neither source should silently invent missing credentials.

For example, salary trade may query `anchor_salary_trade_agent_whitelist` to find candidate proxy users by country and currency, then still needs CSV, login API, or Redis to resolve that proxy user's ticket.

## Extensions

When a new role or rule is detected but not known, write it under:

```yaml
extensions:
  pending:
    - type: role
      name: risk_reviewer
      reason: API field reviewerUid appears in approval steps
      suggested_fields: [reviewerUid, ticket]
```

Pending extensions affect only the current requirement package until a tester confirms them. Promote a repeated extension into this skill only after it appears across multiple requirements.

## Required Output

`account_model.yaml` should include:

- `schema_version`
- `package_id`
- `mode`
- `roles`
- `credential_resolution_order`
- `data_sources`
- `variable_namespace`
- `csv_required`
- `blocking_rules`
- `extensions.pending`

Keep secrets out of the model. Store paths and source names only.
