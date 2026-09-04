from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate schema-driven API test case designs")
    parser.add_argument("openapi", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--package-id", default="")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))
    from quality_hub_backend.services.api_case_design import generate_api_case_design, write_case_design

    spec = json.loads(args.openapi.read_text(encoding="utf-8-sig"))
    payload = generate_api_case_design(spec, args.package_id)
    paths = write_case_design(payload, args.output)
    print(json.dumps({"summary": payload["summary"], "paths": paths}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
