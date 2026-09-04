# Structured Requirement Case Contract

The JSON output must preserve platform-compatible top-level fields:

```json
{
  "schema_version": "1.2",
  "project_id": "project-id",
  "package_id": "requirement-package-id",
  "package_name": "需求名称",
  "requirement_model": {},
  "requirement_gaps": [],
  "coverage_matrix": {},
  "summary": {},
  "cases": []
}
```

Each case must contain:

```json
{
  "id": "REQ_CASE_001",
  "title": "用例标题",
  "requirement_ref": ["REQ-001", "AC-002"],
  "business_goal": "本用例验证的业务价值或规则",
  "scenario_id": "scenario-stable-id",
  "scenario_type": "main_flow|alternate_flow|exception_flow|business_boundary",
  "design_technique": "scenario_analysis|state_transition|decision_table|equivalence_partition|boundary_value|pairwise|error_guessing",
  "priority": "P0|P1|P2|P3",
  "actors": ["applicant", "agent"],
  "account_slots": ["applicant_01", "agent_matched"],
  "preconditions": [],
  "initial_state": {},
  "test_data": {},
  "resource_requirements": [],
  "steps": [
    {
      "step": 1,
      "actor": "applicant",
      "action": "创建业务对象",
      "interface_ref": "POST /resource",
      "extract": {"orderNo": "$.data.orderNo"}
    }
  ],
  "state_path": ["INITIAL", "PENDING", "COMPLETED"],
  "expected_results": {
    "visible": [],
    "api_business": [],
    "state": [],
    "data_evidence": [],
    "audit_and_side_effects": []
  },
  "cleanup_or_compensation": {},
  "evidence_rule_ids": [],
  "automation": {
    "status": "SCRIPT_GENERATION_READY",
    "recommended_tools": ["newman", "jmeter", "pytest"],
    "reason": ""
  },
  "quality_status": "READY",
  "inferred": false,
  "need_review": false,
  "review_notes": []
}
```

## Contract Rules

- `requirement_ref` cannot be empty. When the input has no IDs, create stable local references and mark them inferred.
- `scenario_id` is stable across regenerations unless the business path changes.
- Every variable extracted in `steps` must be consumed by a later step, assertion, cleanup, or evidence query.
- A stateful case needs `initial_state`, `state_path`, and a terminal expected state.
- `resource_requirements` describes needs and source constraints, not secrets.
- `evidence_rule_ids` contains only confirmed rules. Unconfirmed mappings belong in candidate output.
- `recommended_tools` is routing advice. It does not split ownership of the requirement package.
- Existing platform fields may be retained for backward compatibility, but they must not contradict this contract.

## Companion Candidate Outputs

After case review, generation may produce these candidates:

- `account_model.candidate.yaml`
- `resource_manifest.candidate.yaml`
- `evidence_rules.candidates.yaml`
- `outputs/execution-plan.candidate.json`

Promote or merge candidates explicitly. Never replace the corresponding formal asset automatically.
