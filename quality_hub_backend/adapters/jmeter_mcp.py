from __future__ import annotations

from pathlib import Path

from .tool_runner import ToolResult, ToolRunner


class JMeterMcpAdapter:
    """Import an approved JMX and execute it through the Node-based MCP bridge."""

    def __init__(
        self,
        runner: ToolRunner,
        *,
        node_executable: Path,
        bridge_path: Path,
        jmeter_home: Path,
        workspace: Path,
        project_root: Path | None = None,
    ) -> None:
        self.runner = runner
        self.node_executable = node_executable
        self.bridge_path = bridge_path
        self.jmeter_home = jmeter_home
        self.workspace = workspace
        self.project_root = project_root or bridge_path.parent.parent.parent

    async def run_workflow(
        self,
        *,
        workflow_path: Path,
        output_dir: Path,
        self_test: bool = False,
        generate_only: bool = False,
        timeout_seconds: int = 1800,
    ) -> ToolResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)
        command = [
            str(self.node_executable),
            str(self.bridge_path),
            "--workflow",
            str(workflow_path),
            "--output-dir",
            str(output_dir),
            "--jmeter-home",
            str(self.jmeter_home),
            "--workspace",
            str(self.workspace),
            "--project-root",
            str(self.project_root),
            "--execution-timeout-seconds",
            str(timeout_seconds),
        ]
        if self_test:
            command.append("--self-test")
        if generate_only:
            command.append("--generate-only")
        return await self.runner.run(
            command,
            cwd=self.bridge_path.parent,
            timeout_seconds=timeout_seconds,
            report_paths=[
                output_dir / "mcp-imported.jmx",
                output_dir / "result.jtl",
                output_dir / "jmeter-html" / "index.html",
                output_dir / "analysis.json",
                output_dir / "run-summary.json",
            ],
        )
