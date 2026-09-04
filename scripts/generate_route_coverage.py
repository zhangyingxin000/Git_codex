import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quality_hub_backend.api.fastapi_app import app  # noqa: E402
from quality_hub_backend.services.route_coverage import write_route_coverage  # noqa: E402


if __name__ == "__main__":
    result = write_route_coverage(app, ROOT / "tests", ROOT / "docs")
    print(result["json_path"])
    print(result["markdown_path"])
    print(result["summary"])
