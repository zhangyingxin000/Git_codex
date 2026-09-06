from pathlib import Path

import app


ABSOLUTE_MACHINE_MARKERS = (
    "C:\\Users\\DELL",
    "C:/Users/DELL",
    "D:\\apache-jmeter",
    "D:/apache-jmeter",
)


def test_portable_project_path_is_relative():
    assert app._portable_project_path(app.ROOT / "skills" / "demo" / "SKILL.md") == "skills/demo/SKILL.md"


def test_manifest_file_status_uses_portable_path(tmp_path, monkeypatch):
    root = tmp_path / "project"
    asset = root / "requirements" / "demo" / "manifest.json"
    asset.parent.mkdir(parents=True)
    asset.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(app, "ROOT", root)

    status = app._file_status(asset)

    assert status["path"] == "requirements/demo/manifest.json"
    assert status["exists"] is True


def test_jmeter_path_normalizer_replaces_project_and_result_paths():
    text = (
        f"{app.ROOT.as_posix()}/data/accounts.csv\n"
        "D:/apache-jmeter-5.6.3/jmx/demo-result.jtl"
    )

    normalized = app._normalize_portable_jmeter_paths(text, "reports/latest/demo-result.jtl")

    assert "${__P(project_root,.)}/data/accounts.csv" in normalized
    assert "${__P(jmeter_result_jtl,${__P(project_root,.)}/reports/latest/demo-result.jtl)}" in normalized
    assert not any(marker in normalized for marker in ABSOLUTE_MACHINE_MARKERS)


def test_maintained_runtime_assets_have_no_local_machine_paths():
    relative_paths = (
        "config/env.test.yaml",
        "requirements/salary-trade/account_model.yaml",
        "requirements/wealth-level/account_model.yaml",
        "outputs/open-salary-trade-state-machine.ps1",
        "outputs/open-salary-trade-only.ps1",
        "outputs/open-salary-baseline.ps1",
        "outputs/open-wealth-level-only.ps1",
        "outputs/salary-trade-case-driven.jmx",
        "outputs/salary-trade-case-jmeter-manifest.json",
        "outputs/wealth-level-only.jmx",
        "requirements/salary-trade/outputs/jmeter/salary-trade-case-driven.jmx",
        "requirements/salary-trade/outputs/jmeter/jmeter-plan.jmx",
        "requirements/wealth-level/outputs/jmeter/jmeter-plan.jmx",
        "requirements/wealth-level/outputs/jmeter/性能基线.jmx",
    )
    for relative_path in relative_paths:
        path = app.ROOT / relative_path
        assert path.is_file(), relative_path
        text = path.read_text(encoding="utf-8")
        assert not any(marker in text for marker in ABSOLUTE_MACHINE_MARKERS), relative_path


def test_portable_jmeter_assets_remain_valid_xml():
    paths = (
        app.ROOT / "outputs" / "salary-trade-case-driven.jmx",
        app.ROOT / "outputs" / "wealth-level-only.jmx",
        app.ROOT / "requirements" / "salary-trade" / "outputs" / "jmeter" / "jmeter-plan.jmx",
        app.ROOT / "requirements" / "wealth-level" / "outputs" / "jmeter" / "性能基线.jmx",
    )
    for path in paths:
        assert app.summarize_jmeter_jmx(path)["status"] == "PASSED", path
