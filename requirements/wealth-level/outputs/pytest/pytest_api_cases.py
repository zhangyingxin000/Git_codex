import json
import os
import urllib.error
import urllib.request

BASE_URL = os.getenv("AUTOTEST_BASE_URL", "https://test2westarlive.gzxchate.com/")
CASES = [
  {
    "title": "缺失UID参数",
    "method": "GET",
    "path": "/level/exeperience/v2/get",
    "headers": {},
    "payload": "",
    "expected_status": 400
  },
  {
    "title": "非法UID类型",
    "method": "GET",
    "path": "/level/exeperience/v2/get",
    "headers": {},
    "payload": "",
    "expected_status": 400
  }
]


def fill_runtime(value):
    if isinstance(value, dict):
        return {k: fill_runtime(v) for k, v in value.items()}
    if isinstance(value, list):
        return [fill_runtime(v) for v in value]
    text = str(value or "")
    runtime = {}
    try:
        runtime = json.loads(os.getenv("AUTOTEST_RUNTIME_PARAMS_JSON", "{}"))
    except Exception:
        runtime = {}
    runtime.setdefault("ticket", os.getenv("AUTOTEST_RUNTIME_TICKET", ""))
    runtime.setdefault("uid", os.getenv("AUTOTEST_RUNTIME_UID", ""))
    for key, raw in runtime.items():
        text = text.replace("{{" + key + "}}", str(raw))
    return text


def run_case(case):
    case = dict(case)
    case["path"] = fill_runtime(case.get("path", ""))
    case["headers"] = fill_runtime(case.get("headers") or {})
    case["payload"] = fill_runtime(case.get("payload"))
    url = case["path"] if case["path"].startswith("http") else BASE_URL.rstrip("/") + "/" + case["path"].lstrip("/")
    body = case.get("payload")
    data = None if body in ("", None) else (body.encode("utf-8") if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode("utf-8"))
    headers = dict(case.get("headers") or {})
    if data and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=case["method"])
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read(200000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(200000).decode("utf-8", "replace")


def test_api_cases():
    assert BASE_URL, "缺少 AUTOTEST_BASE_URL"
    for case in CASES:
        status, _ = run_case(case)
        assert status == case["expected_status"], f'{case["title"]} expected {case["expected_status"]}, got {status}'
