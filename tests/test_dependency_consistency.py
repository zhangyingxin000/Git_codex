import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _package_name(specification: str) -> str:
    return re.split(r"[<>=!~\[]", specification.strip(), maxsplit=1)[0].lower().replace("_", "-")


def test_pyproject_and_requirements_declare_the_same_direct_dependencies() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    pyproject_names = {_package_name(item) for item in project["dependencies"]}
    requirement_names = {
        _package_name(line)
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert pyproject_names == requirement_names


def test_lock_contains_every_direct_dependency() -> None:
    locked_names = {
        _package_name(line)
        for line in (ROOT / "requirements.lock").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    direct_names = {
        _package_name(line)
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert direct_names <= locked_names
