from pathlib import Path

from quality_hub_backend.api.fastapi_app import app
from quality_hub_backend.services.route_coverage import build_route_coverage, write_route_coverage


ROOT = Path(__file__).resolve().parents[1]


def test_route_coverage_inventory_contains_every_api_route(tmp_path: Path) -> None:
    result = write_route_coverage(app, ROOT / "tests", tmp_path)
    keys = {(row["path"], tuple(row["methods"])) for row in result["routes"]}

    assert result["summary"]["routes"] >= 106
    assert len(keys) == result["summary"]["routes"]
    assert ("/api/health", ("GET",)) in keys
    assert ("/api/tasks", ("POST",)) in keys
    assert Path(result["json_path"]).is_file()
    assert Path(result["markdown_path"]).is_file()


def test_critical_new_routes_have_test_evidence() -> None:
    result = build_route_coverage(app, ROOT / "tests")
    by_path = {row["path"]: row for row in result["routes"]}

    assert by_path["/api/health"]["coverage_status"] == "COVERED"
    assert by_path["/api/tasks/types"]["coverage_status"] == "COVERED"
    assert result["summary"]["p0_unmapped"] == 0
