import copy
import json
import sys
from pathlib import Path


BOUNDARIES = [1, 9, 10, 19, 20, 29, 30, 39, 40, 49, 50, 59, 60, 69, 70, 79, 80, 89, 90, 99, 100]


def build(source_path, output_dir):
    original = json.loads(Path(source_path).read_text(encoding="utf-8-sig"))
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for level in BOUNDARIES:
        payload = copy.deepcopy(original)
        info = payload["data"]["myExperLevelInfo"]
        info["currentLevel"] = level
        info["nextLevel"] = min(100, level + 1)
        info["currentExperLevelValue"] = level * 1_000_000
        info["currentExperValue"] = level * 1_000_000 + (0 if level == 100 else 500_000)
        info["nextExperLevelValue"] = 0 if level == 100 else (level + 1) * 1_000_000
        payload["_mockMeta"] = {"mock": True, "scenario": f"level-{level}", "basis": "real-response-structure", "experienceValues": "synthetic-not-business-config"}
        filename = f"level-{level:03d}.json"
        (output / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append({"name": f"等级 {level}", "file": filename, "currentLevel": level, "type": "boundary"})

    abnormal = {
        "empty-rights": lambda x: x["data"].update({"experRights": []}),
        "missing-user-info": lambda x: x["data"].pop("myExperLevelInfo", None),
        "null-data": lambda x: x.update({"data": None}),
        "duplicate-level-range": lambda x: x["data"]["experRights"].append(copy.deepcopy(x["data"]["experRights"][-1])),
        "invalid-resource-url": lambda x: x["data"]["experRights"][0]["right2"][0].update({"rightImageUrl": "invalid-url"}),
        "missing-arabic-name": lambda x: x["data"]["experRights"][0]["right2"][0].update({"rightArName": ""}),
    }
    for name, mutate in abnormal.items():
        payload = copy.deepcopy(original); mutate(payload)
        payload["_mockMeta"] = {"mock": True, "scenario": name, "basis": "fault-injection"}
        filename = name + ".json"; (output / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append({"name": name, "file": filename, "type": "abnormal"})

    unauthorized = {"code": 401, "message": "unauthorized", "data": None, "_mockMeta": {"mock": True, "scenario": "unauthorized"}}
    (output / "unauthorized.json").write_text(json.dumps(unauthorized, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest.append({"name": "未授权", "file": "unauthorized.json", "type": "auth"})
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: mock_wealth_responses.py REAL_RESPONSE_JSON OUTPUT_DIR")
    print(json.dumps({"generated": len(build(sys.argv[1], sys.argv[2]))}, ensure_ascii=False))
