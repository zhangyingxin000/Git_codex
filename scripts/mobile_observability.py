from __future__ import annotations

import math
import re
import subprocess
import time
from typing import Any


def build_performance_interpretation(performance: dict[str, Any]) -> dict[str, Any]:
    startup = performance.get("startup") or {}
    after = performance.get("after_workflows") or {}
    graphics = after.get("graphics") or {}
    runtime_health = performance.get("runtime_health") or {}

    def metric(
        name: str,
        value: float | int | None,
        unit: str,
        status: str,
        reference: str,
        conclusion: str,
    ) -> dict[str, Any]:
        return {
            "name": name,
            "value": value,
            "unit": unit,
            "status": status,
            "industry_reference": reference,
            "conclusion": conclusion,
        }

    cold_ms = (startup.get("cold") or {}).get("total_time_ms")
    warm_ms = (startup.get("warm") or {}).get("total_time_ms")
    cpu = after.get("process_cpu_percent")
    pss_kb = after.get("total_pss_kb")
    fps = graphics.get("estimated_fps")
    jank = graphics.get("jank_percent")
    signal_count = runtime_health.get("signal_count")
    metrics: list[dict[str, Any]] = []

    if cold_ms is not None:
        cold_status = "PASS" if cold_ms < 2000 else "ACCEPTABLE" if cold_ms <= 3000 else "WARN"
        cold_conclusion = (
            "冷启动表现良好。"
            if cold_status == "PASS"
            else "冷启动尚可，但建议继续缩短首屏初始化。"
            if cold_status == "ACCEPTABLE"
            else "冷启动偏慢，需要拆分首屏初始化任务。"
        )
        metrics.append(metric("冷启动耗时", cold_ms, "ms", cold_status, "<2000ms合格，2000-3000ms可接受", cold_conclusion))
    if warm_ms is not None:
        warm_status = "PASS" if warm_ms < 1000 else "WARN"
        metrics.append(metric("热启动耗时", warm_ms, "ms", warm_status, "<1000ms通常为合格", "热启动响应良好。" if warm_status == "PASS" else "热启动偏慢，需要检查页面恢复和进程重建。"))
    if fps is not None:
        fps_status = "PASS" if fps >= 55 else "ACCEPTABLE" if fps >= 45 else "WARN"
        metrics.append(metric("界面帧率", fps, "FPS", fps_status, ">=55较流畅，45-55可接受，<45需优化", "滑动和动画流畅。" if fps_status == "PASS" else "存在可感知掉帧风险。"))
    if jank is not None:
        jank_status = "PASS" if jank <= 5 else "ACCEPTABLE" if jank <= 10 else "WARN"
        metrics.append(metric("卡顿帧比例", jank, "%", jank_status, "<=5%表现良好，5%-10%需关注", "未观察到明显卡顿。" if jank_status == "PASS" else "需要定位主线程长任务和慢帧。"))
    if cpu is not None:
        cpu_status = "PASS" if cpu <= 60 else "WARN"
        cpu_reference = (
            "Android多核进程统计可超过100%；持续高于60%建议关注，单次采样需结合场景复测"
        )
        cpu_conclusion = "CPU处于当前提醒线内。"
        if cpu_status == "WARN":
            cpu_conclusion = "CPU采样值超过提醒线，功能可通过但需要性能复核。"
        if cpu > 100:
            cpu_conclusion += f" 当前数值约等于持续占用{round(cpu / 100, 2)}个CPU核心。"
        metrics.append(metric("CPU峰值", cpu, "%", cpu_status, cpu_reference, cpu_conclusion))
    if pss_kb is not None:
        metrics.append(metric("PSS内存", round(pss_kb / 1024, 2), "MB", "INFO", "需结合应用规模、设备内存和连续运行趋势判断", "单次PSS用于建立基线，内存泄漏需多轮生命周期或Profiler证据确认。"))
    if signal_count is not None:
        health_status = "PASS" if signal_count == 0 else "FAIL"
        metrics.append(metric("OOM/崩溃/ANR", signal_count, "signals", health_status, "期望为0", "未发现运行时异常信号。" if health_status == "PASS" else "发现运行时异常信号，需要结合logcat定位。"))

    cpu_recommendations = []
    if cpu is not None and cpu > 60:
        cpu_recommendations = [
            "使用 Android Studio CPU Profiler 或 Perfetto 复测同一场景，定位峰值对应的方法和线程。",
            "检查主线程中的图片解码、JSON解析、列表绑定、动画计算和同步I/O。",
            "检查房间页轮询、心跳、音视频处理和重复网络请求是否在页面恢复后叠加执行。",
            "优化无效重绘、布局层级和图片缓存，并在低中高配置设备上重复采样确认趋势。",
        ]
    return {
        "status": "WARN" if any(item["status"] in {"WARN", "FAIL"} for item in metrics) else "PASS",
        "metrics": metrics,
        "cpu_optimization_recommendations": cpu_recommendations,
        "note": "性能结论来自当前设备和当前场景的一次采样；正式基线应至少重复3次并比较中位数或P95。",
    }


def render_performance_interpretation(interpretation: dict[str, Any]) -> str:
    lines = ["# 移动端性能数据解读", ""]
    for item in interpretation.get("metrics") or []:
        lines.append(
            f"- **{item['name']}**：{item['value']}{item['unit']}，{item['conclusion']}"
            f" 参考标准：{item['industry_reference']}。"
        )
    recommendations = interpretation.get("cpu_optimization_recommendations") or []
    if recommendations:
        lines.extend(["", "## CPU峰值后续优化方向", ""])
        lines.extend(f"- {item}" for item in recommendations)
    lines.extend(["", f"> {interpretation.get('note') or ''}", ""])
    return "\n".join(lines)


def run_adb(
    adb_path: str,
    udid: str,
    arguments: list[str],
    timeout_seconds: int = 30,
    check: bool = True,
) -> str:
    completed = subprocess.run(
        [adb_path, "-s", udid, *arguments],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"ADB command failed: {detail}")
    return completed.stdout


def resolve_launcher_component(adb_path: str, udid: str, package: str) -> str:
    output = run_adb(
        adb_path,
        udid,
        ["shell", "cmd", "package", "resolve-activity", "--brief", package],
    )
    for line in reversed(output.splitlines()):
        value = line.strip()
        if "/" in value and "No activity found" not in value:
            return value
    raise RuntimeError(f"launcher activity could not be resolved for {package}")


def parse_startup_timing(output: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {"raw": output.strip()}
    names = {
        "ThisTime": "this_time_ms",
        "TotalTime": "total_time_ms",
        "WaitTime": "wait_time_ms",
    }
    for source_name, target_name in names.items():
        match = re.search(rf"^{source_name}:\s*(\d+)", output, re.MULTILINE)
        if match:
            metrics[target_name] = int(match.group(1))
    status = re.search(r"^Status:\s*(\S+)", output, re.MULTILINE)
    if status:
        metrics["status"] = status.group(1)
    return metrics


def measure_app_start(
    adb_path: str,
    udid: str,
    package: str,
    component: str,
    cold: bool,
    settle_seconds: float = 1.0,
) -> dict[str, Any]:
    if cold:
        run_adb(adb_path, udid, ["shell", "am", "force-stop", package])
    else:
        run_adb(adb_path, udid, ["shell", "input", "keyevent", "KEYCODE_HOME"])
    time.sleep(max(settle_seconds, 0.0))
    arguments = ["shell", "am", "start", "-W"]
    if cold:
        arguments.append("-S")
    arguments.extend(["-n", component])
    metrics = parse_startup_timing(run_adb(adb_path, udid, arguments, timeout_seconds=60))
    metrics["type"] = "cold" if cold else "warm"
    metrics["component"] = component
    return metrics


def parse_meminfo(output: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    total_pss = re.search(r"TOTAL PSS:\s*(\d+)", output)
    if not total_pss:
        total_pss = re.search(r"^\s*TOTAL\s+(\d+)\s+", output, re.MULTILINE)
    if total_pss:
        result["total_pss_kb"] = int(total_pss.group(1))
    native_heap = re.search(r"^\s*Native Heap\s+(\d+)\s+", output, re.MULTILINE)
    if native_heap:
        result["native_heap_pss_kb"] = int(native_heap.group(1))
    java_heap = re.search(r"^\s*(?:Dalvik Heap|Java Heap)\s+(\d+)\s+", output, re.MULTILINE)
    if java_heap:
        result["java_heap_pss_kb"] = int(java_heap.group(1))
    return result


def parse_cpuinfo(output: str, package: str) -> dict[str, Any]:
    process_pattern = re.compile(
        rf"^\s*\+?([\d.]+)%\s+\d+/{re.escape(package)}(?:\S*)?:",
        re.MULTILINE,
    )
    values = [float(value) for value in process_pattern.findall(output)]
    return {"process_cpu_percent": sum(values)} if values else {}


def parse_top_cpu(output: str, package: str) -> dict[str, Any]:
    pattern = re.compile(
        rf"^\s*\d+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S\s+"
        rf"([\d.]+)\s+[\d.]+\s+\S+\s+{re.escape(package)}(?:\S*)?\s*$",
        re.MULTILINE,
    )
    values = [float(value) for value in pattern.findall(output)]
    return {"process_cpu_percent": sum(values), "cpu_source": "top"} if values else {}


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return round(ordered[index], 3)


def parse_gfxinfo_framestats(output: str, frame_budget_ms: float = 16.67) -> dict[str, Any]:
    frames: list[tuple[int, int]] = []
    intended_index = 1
    completed_index = 16
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("Flags,"):
            columns = [column.strip() for column in line.rstrip(",").split(",")]
            if "IntendedVsync" in columns and "FrameCompleted" in columns:
                intended_index = columns.index("IntendedVsync")
                completed_index = columns.index("FrameCompleted")
            continue
        if not line or not re.match(r"^\d+,", line):
            continue
        fields = line.split(",")
        if len(fields) <= max(intended_index, completed_index):
            continue
        try:
            flags = int(fields[0])
            intended_vsync = int(fields[intended_index])
            frame_completed = int(fields[completed_index])
        except ValueError:
            continue
        if flags == 0 and intended_vsync > 0 and frame_completed >= intended_vsync:
            frames.append((intended_vsync, frame_completed))
    if not frames:
        return {"rendered_frames": 0}

    frame_times_ms = [(completed - intended) / 1_000_000 for intended, completed in frames]
    janky_frames = sum(duration > frame_budget_ms for duration in frame_times_ms)
    intended_times = sorted(intended for intended, _ in frames)
    active_gap_ns = 250_000_000
    active_intervals = [
        current - previous
        for previous, current in zip(intended_times, intended_times[1:], strict=False)
        if 0 < current - previous <= active_gap_ns
    ]
    group_count = 1 + sum(
        current - previous > active_gap_ns
        for previous, current in zip(intended_times, intended_times[1:], strict=False)
    )
    frame_interval_seconds = max(frame_budget_ms / 1000, 0.001)
    active_seconds = (
        sum(active_intervals) / 1_000_000_000 + group_count * frame_interval_seconds
    )
    return {
        "rendered_frames": len(frames),
        "estimated_fps": round(len(frames) / max(active_seconds, 0.001), 2),
        "active_render_seconds": round(active_seconds, 3),
        "janky_frames": janky_frames,
        "jank_percent": round(janky_frames * 100 / len(frames), 2),
        "frame_time_p50_ms": _percentile(frame_times_ms, 0.50),
        "frame_time_p90_ms": _percentile(frame_times_ms, 0.90),
        "frame_time_p95_ms": _percentile(frame_times_ms, 0.95),
        "frame_time_p99_ms": _percentile(frame_times_ms, 0.99),
        "frame_budget_ms": frame_budget_ms,
    }


def reset_graphics(adb_path: str, udid: str, package: str) -> None:
    run_adb(adb_path, udid, ["shell", "dumpsys", "gfxinfo", package, "reset"])


def collect_device_metrics(
    adb_path: str,
    udid: str,
    package: str,
    include_graphics: bool = False,
    frame_budget_ms: float = 16.67,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {"captured_at_epoch_ms": int(time.time() * 1000)}
    metrics.update(parse_meminfo(run_adb(adb_path, udid, ["shell", "dumpsys", "meminfo", package])))
    cpu_metrics = parse_cpuinfo(
        run_adb(adb_path, udid, ["shell", "dumpsys", "cpuinfo"]), package
    )
    if not cpu_metrics or cpu_metrics.get("process_cpu_percent") == 0:
        process_ids = run_adb(
            adb_path, udid, ["shell", "pidof", package], check=False
        ).split()
        if process_ids:
            top_output = run_adb(
                adb_path,
                udid,
                ["shell", "top", "-b", "-n", "1", "-p", process_ids[0]],
                check=False,
            )
            cpu_metrics = parse_top_cpu(top_output, package) or cpu_metrics
    metrics.update(cpu_metrics)
    if include_graphics:
        graphics = run_adb(
            adb_path,
            udid,
            ["shell", "dumpsys", "gfxinfo", package, "framestats"],
        )
        metrics["graphics"] = parse_gfxinfo_framestats(graphics, frame_budget_ms)
    return metrics


def parse_runtime_health(logcat: str, package: str) -> dict[str, Any]:
    signal_patterns = {
        "out_of_memory": re.compile(r"OutOfMemoryError", re.IGNORECASE),
        "fatal_exception": re.compile(r"FATAL EXCEPTION", re.IGNORECASE),
        "anr": re.compile(rf"ANR in\s+{re.escape(package)}", re.IGNORECASE),
        "process_died": re.compile(
            rf"Process\s+{re.escape(package)}(?:\S*)?\s+.*(?:died|has died)",
            re.IGNORECASE,
        ),
    }
    matches: list[dict[str, str]] = []
    lines = logcat.splitlines()
    for index, line in enumerate(lines):
        context = "\n".join(lines[max(0, index - 4) : index + 5])
        for signal_name, pattern in signal_patterns.items():
            requires_package_context = signal_name in {"out_of_memory", "fatal_exception"}
            if pattern.search(line) and (not requires_package_context or package in context):
                matches.append({"type": signal_name, "line": line.strip()})
                break
    return {
        "status": "FAIL" if matches else "PASS",
        "signal_count": len(matches),
        "signals": matches[:100],
    }


def evaluate_performance(
    startup: dict[str, Any],
    before: dict[str, Any],
    after: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add_check(name: str, actual: float | None, limit: float | None, mode: str) -> None:
        if actual is None or limit is None:
            return
        passed = actual <= limit if mode == "max" else actual >= limit
        checks.append(
            {
                "name": name,
                "actual": actual,
                "limit": limit,
                "status": "PASS" if passed else "FAIL",
            }
        )

    add_check(
        "cold_start_ms",
        startup.get("cold", {}).get("total_time_ms"),
        thresholds.get("max_cold_start_ms"),
        "max",
    )
    add_check(
        "warm_start_ms",
        startup.get("warm", {}).get("total_time_ms"),
        thresholds.get("max_warm_start_ms"),
        "max",
    )
    add_check(
        "memory_total_pss_kb",
        after.get("total_pss_kb"),
        thresholds.get("max_total_pss_kb"),
        "max",
    )
    before_pss = before.get("total_pss_kb")
    after_pss = after.get("total_pss_kb")
    memory_growth = after_pss - before_pss if before_pss is not None and after_pss is not None else None
    add_check(
        "memory_growth_kb",
        memory_growth,
        thresholds.get("max_memory_growth_kb"),
        "max",
    )
    add_check(
        "process_cpu_percent",
        after.get("process_cpu_percent"),
        thresholds.get("max_cpu_percent"),
        "max",
    )
    graphics = after.get("graphics") or {}
    add_check("estimated_fps", graphics.get("estimated_fps"), thresholds.get("min_fps"), "min")
    add_check(
        "jank_percent",
        graphics.get("jank_percent"),
        thresholds.get("max_jank_percent"),
        "max",
    )
    failed = [check for check in checks if check["status"] == "FAIL"]
    return {
        "status": "FAIL" if failed else "PASS",
        "checks": checks,
        "memory_growth_kb": memory_growth,
        "memory_leak_assessment": (
            "SUSPECTED_TREND" if memory_growth is not None and memory_growth > 0 else "NOT_OBSERVED"
        ),
        "note": (
            "A single run can reveal abnormal growth but cannot prove a memory leak; "
            "repeat the same scenario and inspect the trend or profiler evidence."
        ),
    }
