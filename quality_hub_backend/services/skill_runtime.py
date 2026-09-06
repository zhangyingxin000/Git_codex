from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


YamlLoader = Callable[[Path], dict[str, Any]]


class SkillRuntime:
    def __init__(self, skill_root: Path, yaml_loader: YamlLoader):
        self.skill_root = Path(skill_root)
        self.yaml_loader = yaml_loader

    def load_rules(
        self,
        skill_name: str,
        *,
        required: bool = False,
        fallback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        root = self.skill_root / skill_name
        skill_path = root / "SKILL.md"
        rules_path = root / "rules.yaml"
        if required and (not skill_path.is_file() or not rules_path.is_file()):
            raise FileNotFoundError(f"Skill不完整：skills/{skill_name} 需要 SKILL.md 和 rules.yaml")
        rules = self.yaml_loader(rules_path) if rules_path.is_file() else {}
        if not rules:
            rules = dict(fallback or {})
        return {
            "skill": str(rules.get("skill") or skill_name),
            "schema_version": str(rules.get("schema_version") or "1.0"),
            "skill_path": str(skill_path),
            "rules_path": str(rules_path),
            "rules": rules,
            "available": skill_path.is_file() and bool(rules),
        }

    def load_markdown_contract(
        self,
        skill_name: str,
        *,
        purpose: str,
        inputs: list[str],
        outputs: list[str],
        principles: list[str],
    ) -> dict[str, Any]:
        path = self.skill_root / skill_name / "SKILL.md"
        return {
            "path": str(path),
            "skill": skill_name,
            "available": path.is_file(),
            "body": path.read_text(encoding="utf-8", errors="replace") if path.is_file() else "",
            "purpose": purpose,
            "inputs": inputs,
            "outputs": outputs,
            "principles": principles,
        }

    @staticmethod
    def structured_case_quality_gate(cases: list[dict[str, Any]], policy: dict[str, Any] | None = None) -> dict[str, Any]:
        case_ids = [str(item.get("id") or "").strip() for item in cases]
        checks = {
            "cases_generated": bool(cases),
            "case_ids_unique": len(case_ids) == len(set(case_ids)) and all(case_ids),
            "requirement_traceability": all(str((item.get("traceability") or {}).get("requirement_ref") or "").strip() for item in cases),
            "expected_results_complete": all(bool(item.get("expected_results")) for item in cases),
            "automation_classified": all(bool(item.get("automation_readiness") or item.get("automation_status")) for item in cases),
        }
        return {
            "status": "PASS" if all(checks.values()) else "REVIEW_REQUIRED",
            "checks": checks,
            "policy": policy or {},
        }
