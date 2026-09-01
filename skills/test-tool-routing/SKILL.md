---
name: test-tool-routing
description: Build a scenario-level execution plan for a requirement package, keeping Newman, JMeter, pytest, and manual review under each business scenario instead of splitting maintenance by tool.
metadata:
  short-description: Plan scenario-level Newman/JMeter/pytest/manual execution
---

# Scenario Execution Planning Skill

## Purpose

Create a maintainable execution plan for one requirement package.

Do not split one business requirement into unrelated Newman, JMeter, and pytest worklists. A requirement package stays as the maintenance unit, and each business scenario owns the tool tasks needed to verify it.

The platform is the orchestration hub. Newman, JMeter, pytest, and manual review remain separate execution methods with different responsibilities:

- Newman runs simple API regression and smoke checks.
- JMeter runs complex workflows, multi-account state machines, loops, concurrency, and performance.
- pytest runs deep verification after execution, especially HTTP plus DB/Redis evidence analysis.
- Manual review is used for long waits, backend operations, irreversible actions, or missing runnable data.

## Planning Rules

Use the selected requirement package, structured test cases, account model, evidence rules, and runtime data strategy.

Do not route by HTTP method alone. A `POST` read-style endpoint can still be Newman, while a `GET` that depends on order state, cross-role permissions, extracted variables, or DB/Redis evidence may belong to a JMeter or pytest task.

For each scenario, produce tool tasks:

- Add `newman` when the scenario has stateless read APIs, authentication smoke, simple contract checks, or reusable preflight calls.
- Add `jmeter` when the scenario needs ordered steps, extracted variables, role switching, multi-account data, state transitions, loops, concurrency, or performance metrics.
- Add `pytest` when the scenario needs post-run DB/Redis evidence checks, generated report replay, or deep assertions across HTTP and storage.
- Add `manual` when the scenario needs operations staff, background jobs, 12/24 hour waiting, irreversible data changes, or unavailable runnable data.

Keep the output scenario-first:

- scenario -> cases -> tool tasks -> reports -> human review
- not tool -> cases -> reports

## Output Contract

Every execution plan should include:

- requirement package id and name
- scenario id, name, business goal, and status
- related test case ids and titles
- tool tasks for Newman, JMeter, pytest, and manual review
- runtime data needs and blockers
- DB/Redis evidence rules and maintenance targets
- report targets grouped by scenario
- summary counts by scenario status and tool

The execution plan is advisory. It should be consumed by script generators when possible, but it must not overwrite official test cases, evidence rules, account models, or JMeter scripts without human confirmation.
