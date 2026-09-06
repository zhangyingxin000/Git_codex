import json

import pytest

from quality_hub_backend.services.skill_runtime import SkillRuntime


def json_loader(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def test_skill_runtime_loads_rules_and_quality_gate(tmp_path) -> None:
    root = tmp_path / "skills"
    skill = root / "requirement-cases"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# Skill", encoding="utf-8")
    (skill / "rules.yaml").write_text(json.dumps({"schema_version": "2.0", "skill": "requirement-cases", "quality_gate": {"required": True}}), encoding="utf-8")
    runtime = SkillRuntime(root, json_loader)

    contract = runtime.load_rules("requirement-cases", required=True)
    gate = runtime.structured_case_quality_gate([{
        "id": "case-1",
        "traceability": {"requirement_ref": "REQ-1"},
        "expected_results": ["成功"],
        "automation_readiness": "READY",
    }], contract["rules"]["quality_gate"])

    assert contract["schema_version"] == "2.0"
    assert contract["available"] is True
    assert gate["status"] == "PASS"


def test_required_skill_rejects_incomplete_directory(tmp_path) -> None:
    runtime = SkillRuntime(tmp_path, json_loader)

    with pytest.raises(FileNotFoundError, match="Skill不完整"):
        runtime.load_rules("missing", required=True)


def test_markdown_contract_exposes_availability_without_business_dependency(tmp_path) -> None:
    skill = tmp_path / "pytest-review"
    skill.mkdir()
    (skill / "SKILL.md").write_text("review rules", encoding="utf-8")
    runtime = SkillRuntime(tmp_path, json_loader)

    contract = runtime.load_markdown_contract(
        "pytest-review",
        purpose="复盘",
        inputs=["result.json"],
        outputs=["review.json"],
        principles=["只分析不自动修改"],
    )

    assert contract["available"] is True
    assert contract["body"] == "review rules"
