import asyncio
from pathlib import Path

from quality_hub_backend.adapters import JMeterMcpAdapter, ToolResult


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


def test_jmeter_mcp_adapter_builds_portable_bridge_command(tmp_path: Path) -> None:
    runner = RecordingRunner()
    bridge = tmp_path / "tools" / "jmeter-mcp" / "bridge.mjs"
    workflow = tmp_path / "workflow.json"
    adapter = JMeterMcpAdapter(
        runner,
        node_executable=Path("node"),
        bridge_path=bridge,
        jmeter_home=tmp_path / "jmeter",
        workspace=tmp_path / "work" / "jmeter-mcp",
    )

    result = asyncio.run(
        adapter.run_workflow(
            workflow_path=workflow,
            output_dir=tmp_path / "reports" / "mcp-poc",
            self_test=True,
            generate_only=True,
            timeout_seconds=90,
        )
    )

    assert result.passed
    assert runner.call is not None
    command = runner.call["command"]
    assert command[:2] == ["node", str(bridge)]
    assert command[command.index("--workflow") + 1] == str(workflow)
    assert command[command.index("--jmeter-home") + 1] == str(tmp_path / "jmeter")
    assert command[command.index("--project-root") + 1] == str(tmp_path)
    assert command[command.index("--execution-timeout-seconds") + 1] == "90"
    assert "--self-test" in command
    assert "--generate-only" in command
    assert runner.call["cwd"] == bridge.parent
    assert runner.call["report_paths"][2].name == "index.html"
