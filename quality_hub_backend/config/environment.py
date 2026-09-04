from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


def parse_simple_yaml_value(value: Any) -> Any:
    text = str(value or "").strip()
    if not text:
        return ""
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if text.startswith("[") and text.endswith("]"):
        try:
            return json.loads(text.replace("'", '"'))
        except Exception:
            return [item.strip().strip('"').strip("'") for item in text[1:-1].split(",") if item.strip()]
    if re.fullmatch(r"-?\d+", text):
        try:
            return int(text)
        except ValueError:
            return text
    if re.fullmatch(r"-?\d+\.\d+", text):
        try:
            return float(text)
        except ValueError:
            return text
    return text


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset required by portable environment files."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in str(text or "").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if not value.strip():
            node: dict[str, Any] = {}
            parent[key.strip()] = node
            stack.append((indent, node))
        else:
            parent[key.strip()] = parse_simple_yaml_value(value)
    return root


def load_yaml_file(path: Path) -> tuple[dict[str, Any], str]:
    path = Path(path)
    if not path.is_file():
        return {}, "missing"
    text = path.read_text(encoding="utf-8")
    try:
        import yaml

        loaded = yaml.safe_load(text) or {}
        return (loaded if isinstance(loaded, dict) else {}), "PyYAML"
    except Exception:
        return parse_simple_yaml(text), "fallback"


def deep_get(mapping: Any, dotted: str, default: Any = None) -> Any:
    current = mapping
    for part in str(dotted).split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def deep_merge(base: dict[str, Any] | None, override: dict[str, Any] | None) -> dict[str, Any]:
    result = dict(base or {})
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_environment_config(config_dir: Path, env_name: str | None = None) -> tuple[dict[str, Any], str]:
    env = str(env_name or os.getenv("AUTOTEST_ENV") or "test").strip() or "test"
    example, example_backend = load_yaml_file(config_dir / "env.example.yaml")
    concrete, concrete_backend = load_yaml_file(config_dir / f"env.{env}.yaml")
    data_sources, source_backend = load_yaml_file(config_dir / "data-sources.yaml")
    config = deep_merge(deep_merge(example, concrete), data_sources)
    config.setdefault("project", {})
    config.setdefault("tools", {})
    config.setdefault("data_sources", {})
    config.setdefault("accounts", {})
    config.setdefault("reports", {})
    config["env_file"] = str(config_dir / f"env.{env}.yaml")
    config["env_name"] = env
    backends = {example_backend, concrete_backend, source_backend}
    backend = "PyYAML" if "PyYAML" in backends else "fallback"
    return config, backend
