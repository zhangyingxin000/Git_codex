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


def test_platform_scripts_reference_current_jmeter_mcp_assets() -> None:
    verification = (ROOT / "verify-migration.ps1").read_text(encoding="utf-8")
    launcher = (ROOT / "platform.ps1").read_text(encoding="utf-8")

    assert "quality_hub_backend\\adapters\\jmeter_mcp.py" in verification
    assert "quality_hub_backend\\adapters\\jmeter.py" not in verification
    assert "tests/test_jmeter_mcp_adapter.py" in launcher
    assert "tests/test_jmeter_adapter.py" not in launcher


def test_platform_exposes_a_reported_ci_quality_gate() -> None:
    launcher = (ROOT / "platform.ps1").read_text(encoding="utf-8")
    runner = ROOT / "scripts" / "run_ci.py"
    jenkinsfile = ROOT / "Jenkinsfile"

    assert '"ci"' in launcher
    assert "scripts\\run_ci.py" in launcher
    assert runner.is_file()
    assert jenkinsfile.is_file()
    assert "platform.cmd ci" in jenkinsfile.read_text(encoding="utf-8")


def test_platform_exposes_configured_external_cli_pipeline() -> None:
    launcher = (ROOT / "platform.ps1").read_text(encoding="utf-8")
    runner = ROOT / "scripts" / "run_external_ci.py"
    example = ROOT / "config" / "ci-tools.example.yaml"
    jenkins = (ROOT / "Jenkinsfile").read_text(encoding="utf-8")

    assert '"ci-tools"' in launcher
    assert runner.is_file()
    assert example.is_file()
    assert "AUTOTEST_CI_TOOLS_CONFIG" in jenkins
    assert "reports/ci-tools" in jenkins


def test_platform_exposes_quality_and_android_cli_layers() -> None:
    launcher = (ROOT / "platform.ps1").read_text(encoding="utf-8")
    jenkins = (ROOT / "Jenkinsfile").read_text(encoding="utf-8")

    for path in (
        ROOT / "requirements-ci.lock",
        ROOT / "package-lock.json",
        ROOT / ".secrets.baseline",
        ROOT / "setup-ci.ps1",
        ROOT / "setup-mobile.ps1",
        ROOT / "scripts" / "generate_allure_report.py",
        ROOT / "scripts" / "run_mobile_ci.py",
        ROOT / "config" / "mobile-ci.example.yaml",
    ):
        assert path.is_file(), path

    assert '"setup-ci"' in launcher
    assert '"setup-mobile"' in launcher
    assert '"mobile-ci"' in launcher
    assert "AUTOTEST_MOBILE_CONFIG" in jenkins
    assert "BrowserStack" not in jenkins


def test_mobile_launcher_writes_utf8_logs_with_windows_powershell() -> None:
    launcher = (ROOT / "platform.ps1").read_text(encoding="utf-8")

    assert "Tee-Object -FilePath $mobileConsole -Encoding" not in launcher
    assert "[IO.File]::WriteAllText($mobileConsole, $mobileConsoleText, $utf8NoBom)" in launcher
