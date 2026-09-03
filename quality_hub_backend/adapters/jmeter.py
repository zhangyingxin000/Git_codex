from __future__ import annotations

from pathlib import Path

from .tool_runner import ToolResult, ToolRunner


class JMeterAdapter:
    def __init__(self, runner: ToolRunner, executable: Path) -> None:
        self.runner = runner
        self.executable = executable

    async def run_plan(
        self,
        *,
        plan_path: Path,
        output_dir: Path,
        properties: dict[str, str],
    ) -> ToolResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        jtl_path = output_dir / "result.jtl"
        html_dir = output_dir / "html"
        command = [
            str(self.executable),
            "-n",
            "-t",
            str(plan_path),
            "-l",
            str(jtl_path),
            "-e",
            "-o",
            str(html_dir),
            *[f"-J{key}={value}" for key, value in properties.items()],
        ]
        return await self.runner.run(
            command,
            cwd=plan_path.parent,
            timeout_seconds=1800,
            report_paths=[jtl_path, html_dir / "index.html"],
        )
