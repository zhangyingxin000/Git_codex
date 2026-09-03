import asyncio
from pathlib import Path

from quality_hub_backend.adapters import JMeterAdapter, ToolResult


class RecordingRunner:
    def __init__(self) -> None:
        self.call = None

    async def run(self, command, *, cwd, timeout_seconds, report_paths):
        self.call = {
            "command": command,
            "cwd": cwd,
            "timeout_seconds": timeout_seconds,
            "report_paths": report_paths,
        }
        return ToolResult(command, 0, "ok", "", report_paths)


def test_jmeter_adapter_import_and_command(tmp_path: Path) -> None:
    runner = RecordingRunner()
    adapter = JMeterAdapter(runner, Path("jmeter"))
    plan = tmp_path / "plan.jmx"
    plan.write_text("<jmeterTestPlan />", encoding="utf-8")

    result = asyncio.run(
        adapter.run_plan(
            plan_path=plan,
            output_dir=tmp_path / "report",
            properties={"threads": "2", "demo_mode": "true"},
        )
    )

    assert result.passed
    assert runner.call is not None
    assert runner.call["cwd"] == tmp_path
    assert "-Jthreads=2" in runner.call["command"]
    assert "-Jdemo_mode=true" in runner.call["command"]
    assert runner.call["report_paths"][0].name == "result.jtl"
