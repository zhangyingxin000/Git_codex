from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    report_paths: list[Path]

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


class ToolRunner:
    async def run(
        self,
        command: list[str],
        *,
        cwd: Path,
        timeout_seconds: int = 600,
        report_paths: list[Path] | None = None,
    ) -> ToolResult:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            process.kill()
            stdout, stderr = await process.communicate()
            return ToolResult(command, 124, stdout.decode("utf-8", "replace"), stderr.decode("utf-8", "replace"), report_paths or [])
        return ToolResult(
            command=command,
            exit_code=process.returncode or 0,
            stdout=stdout.decode("utf-8", "replace"),
            stderr=stderr.decode("utf-8", "replace"),
            report_paths=report_paths or [],
        )
