from quality_hub_backend.services.review_memory import load_review_memory, persist_review_memory


def review(run_id, status="PASSED"):
    return {
        "package_id": "pkg",
        "run_id": run_id,
        "status": status,
        "created_at": f"2026-09-04T10:00:0{run_id[-1]}+08:00",
        "conclusion": f"结论 {run_id}",
        "summary": {"p0": int(status == "FAILED")},
        "root_cause_categories": {"authentication": 1} if status == "FAILED" else {},
        "next_actions": ["人工复核"],
        "findings": [{"level": "P0", "category": "authentication", "title": "认证失败", "evidence": "secret", "recommendation": "更新凭证"}],
    }


def test_review_memory_keeps_latest_condensed_conclusions(tmp_path) -> None:
    path = tmp_path / "outputs" / "ai-review-conclusions.json"

    persist_review_memory(path, review("run-1", "FAILED"), keep=2)
    result = persist_review_memory(path, review("run-2"), keep=2)

    assert result["latest"]["run_id"] == "run-2"
    assert [item["run_id"] for item in result["history"]] == ["run-2", "run-1"]
    assert "evidence" not in result["history"][1]["findings"][0]
    assert load_review_memory(path)["latest"]["conclusion"] == "结论 run-2"


def test_review_memory_replaces_same_run_instead_of_duplicating(tmp_path) -> None:
    path = tmp_path / "memory.json"
    persist_review_memory(path, review("run-1", "FAILED"))
    result = persist_review_memory(path, review("run-1", "PASSED"))

    assert len(result["history"]) == 1
    assert result["latest"]["status"] == "PASSED"
