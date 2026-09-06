import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { computeAggregate } from "./node_modules/jmeter-mcp-server/dist/report/aggregate.js";
import { parseJtl } from "./node_modules/jmeter-mcp-server/dist/report/jtlParser.js";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const MCP_ENTRY = path.join(
  ROOT,
  "node_modules",
  "jmeter-mcp-server",
  "dist",
  "index.js",
);
const REQUIRED_TOOLS = [
  "import_test_plan",
  "get_test_plan_xml",
  "execute_test_plan",
  "get_execution_status",
  "stop_execution",
  "get_execution_report",
];

function readArguments(argv) {
  const result = {
    selfTest: false,
    generateOnly: false,
    executionTimeoutSeconds: 1800,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index];
    if (key === "--self-test") {
      result.selfTest = true;
      continue;
    }
    if (key === "--generate-only") {
      result.generateOnly = true;
      continue;
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`Missing value for ${key}`);
    }
    index += 1;
    if (key === "--workflow") result.workflowPath = path.resolve(value);
    else if (key === "--output-dir") result.outputDir = path.resolve(value);
    else if (key === "--jmeter-home") result.jmeterHome = path.resolve(value);
    else if (key === "--workspace") result.workspace = path.resolve(value);
    else if (key === "--project-root") result.projectRoot = path.resolve(value);
    else if (key === "--execution-timeout-seconds") {
      result.executionTimeoutSeconds = Math.max(1, Number(value));
    }
    else throw new Error(`Unknown argument: ${key}`);
  }
  result.jmeterHome =
    result.jmeterHome ||
    (process.env.AUTOTEST_JMETER_HOME
      ? path.resolve(process.env.AUTOTEST_JMETER_HOME)
      : undefined) ||
    (process.env.JMETER_HOME ? path.resolve(process.env.JMETER_HOME) : undefined);
  result.workspace = result.workspace || path.resolve(ROOT, "../../work/jmeter-mcp");
  result.projectRoot = result.projectRoot || path.resolve(ROOT, "../..");
  if (!result.workflowPath) throw new Error("--workflow is required");
  if (!result.outputDir) throw new Error("--output-dir is required");
  if (!result.jmeterHome) {
    throw new Error("--jmeter-home, AUTOTEST_JMETER_HOME, or JMETER_HOME is required");
  }
  return result;
}

function resolveProjectPath(projectRoot, value) {
  return path.isAbsolute(value) ? value : path.resolve(projectRoot, value);
}

function writeProgress(outputDir, phase, percent, message, detail = {}) {
  writeFileSync(
    path.join(outputDir, "execution-progress.json"),
    JSON.stringify({
      phase,
      percent: Math.max(0, Math.min(100, Number(percent) || 0)),
      message,
      updated_at: new Date().toISOString(),
      ...detail,
    }, null, 2),
    "utf-8",
  );
}

function parseToolResult(result, toolName) {
  const text = result.content?.find((item) => item.type === "text")?.text;
  if (result.isError || !text) {
    throw new Error(`${toolName} failed: ${text || "empty MCP response"}`);
  }
  return JSON.parse(text);
}

async function callTool(client, name, args) {
  return parseToolResult(
    await client.callTool({ name, arguments: args }),
    name,
  );
}

function runCommand(command, args, cwd) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      shell: false,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) resolve({ stdout, stderr });
      else reject(new Error(`${command} exited with ${code}\n${stdout}\n${stderr}`));
    });
  });
}

function inheritedEnvironment() {
  return Object.fromEntries(
    Object.entries(process.env).filter(([, value]) => typeof value === "string"),
  );
}

function ensureNoRawCredentials(workflow) {
  if (!workflow.source_jmx) {
    throw new Error(
      "source_jmx is required. Typed MCP JMX generation has been removed; run the JMeter Skill gate before MCP execution.",
    );
  }
  if (workflow.thread_groups || workflow.variables) {
    throw new Error(
      "Typed thread_groups/variables are no longer accepted by the MCP execution bridge.",
    );
  }
  const gateStatus = workflow.metadata?.preflight_status;
  if (gateStatus && !["PASS", "PASS_WITH_WARNINGS"].includes(gateStatus)) {
    throw new Error(`JMeter Skill preflight did not pass: ${gateStatus}`);
  }
}

async function startSelfTestServer() {
  const server = createServer((request, response) => {
    if (request.method === "GET" && request.url === "/api/health") {
      const body = JSON.stringify({ ok: true, engine: "jmeter-mcp", mode: "self-test" });
      response.writeHead(200, {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": Buffer.byteLength(body),
        "X-Request-Id": `mcp-${Date.now()}`,
      });
      response.end(body);
      return;
    }
    response.writeHead(404, { "Content-Type": "application/json" });
    response.end(JSON.stringify({ ok: false }));
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  if (!address || typeof address === "string") {
    throw new Error("Could not resolve self-test server port");
  }
  return { server, url: `http://127.0.0.1:${address.port}/api/health` };
}

function buildSelfTestJmx(url) {
  const target = new URL(url);
  return `<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="JMeter MCP import self-test" enabled="true">
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments"><collectionProp name="Arguments.arguments"/></elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Import and execute" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController"><boolProp name="LoopController.continue_forever">false</boolProp><stringProp name="LoopController.loops">1</stringProp></elementProp>
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">1</stringProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="GET self-test health" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments"><collectionProp name="Arguments.arguments"/></elementProp>
          <stringProp name="HTTPSampler.domain">${target.hostname}</stringProp>
          <stringProp name="HTTPSampler.port">${target.port}</stringProp>
          <stringProp name="HTTPSampler.protocol">${target.protocol.replace(":", "")}</stringProp>
          <stringProp name="HTTPSampler.path">${target.pathname}</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
        </HTTPSamplerProxy>
        <hashTree>
          <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="HTTP 200" enabled="true">
            <collectionProp name="Asserion.test_strings"><stringProp name="200">200</stringProp></collectionProp>
            <stringProp name="Assertion.test_field">Assertion.response_code</stringProp>
            <boolProp name="Assertion.assume_success">false</boolProp>
            <intProp name="Assertion.test_type">8</intProp>
          </ResponseAssertion>
          <hashTree/>
        </hashTree>
        <ResultCollector guiclass="StatVisualizer" testclass="ResultCollector" testname="Execution result writer" enabled="true">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <stringProp name="filename"></stringProp>
        </ResultCollector>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>`;
}

async function buildPlan(client, workflow, projectRoot) {
  const imported = await callTool(client, "import_test_plan", {
    filePath: resolveProjectPath(projectRoot, workflow.source_jmx),
    name: workflow.name,
  });
  return { ...imported, imported: true };
}

function finiteNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function monitoredRequestMetrics(report) {
  const rows = Array.isArray(report?.byLabel) ? report.byLabel : [];
  const requestRows = rows.filter(
    (item) => !String(item?.label || "").startsWith("TX::")
      && !String(item?.label || "").startsWith("TRANSACTION::"),
  );
  const measured = requestRows.length ? requestRows : rows;
  const samples = measured.reduce(
    (total, item) => total + finiteNumber(item?.count),
    0,
  );
  const errors = measured.reduce(
    (total, item) => total + finiteNumber(
      item?.errors,
      finiteNumber(item?.count) * finiteNumber(item?.errorPct) / 100,
    ),
    0,
  );
  return {
    samples,
    errors: Math.round(errors),
    error_rate_pct: samples ? Number((errors / samples * 100).toFixed(2)) : 0,
    p95_ms: measured.length
      ? Math.max(...measured.map((item) => finiteNumber(item?.p95Ms)))
      : 0,
    p99_ms: measured.length
      ? Math.max(...measured.map((item) => finiteNumber(item?.p99Ms)))
      : 0,
  };
}

function measuredRequestSamples(samples, warmupSamplesPerLabel) {
  const requestSamples = samples.filter(
    (item) => !String(item?.label || "").startsWith("TX::")
      && !String(item?.label || "").startsWith("TRANSACTION::"),
  );
  const warmupLimit = Math.max(0, Math.floor(finiteNumber(warmupSamplesPerLabel)));
  if (!warmupLimit) return requestSamples;

  const grouped = new Map();
  for (const sample of requestSamples) {
    const label = String(sample?.label || "");
    const rows = grouped.get(label) || [];
    rows.push(sample);
    grouped.set(label, rows);
  }
  const measured = [];
  for (const rows of grouped.values()) {
    rows.sort((left, right) => finiteNumber(left?.timestamp) - finiteNumber(right?.timestamp));
    const excluded = Math.min(warmupLimit, Math.max(0, rows.length - 1));
    measured.push(...rows.slice(excluded));
  }
  return measured;
}

function autoStopConfiguration(workflow) {
  const supplied = workflow?.auto_stop || {};
  const thresholds = workflow?.thresholds || {};
  return {
    enabled: supplied.enabled !== false,
    sample_interval_seconds: Math.max(1, finiteNumber(supplied.sample_interval_seconds, 2)),
    grace_period_seconds: Math.max(0, finiteNumber(supplied.grace_period_seconds, 5)),
    min_samples: Math.max(1, finiteNumber(supplied.min_samples, 10)),
    latency_consecutive_windows: Math.max(
      2,
      finiteNumber(supplied.latency_consecutive_windows, 2),
    ),
    error_consecutive_windows: Math.max(
      1,
      finiteNumber(supplied.error_consecutive_windows, 1),
    ),
    warmup_samples_per_label: Math.max(
      0,
      finiteNumber(supplied.warmup_samples_per_label, 0),
    ),
    max_error_rate_pct: thresholds.max_error_rate_pct ?? thresholds.max_error_rate ?? null,
    max_p95_ms: thresholds.max_p95_ms ?? null,
    max_p99_ms: thresholds.max_p99_ms ?? null,
  };
}

function exceeded(metric, threshold, allowZero = false) {
  if (threshold === null || threshold === undefined || threshold === "") return false;
  const normalized = finiteNumber(threshold, -1);
  return (allowZero ? normalized >= 0 : normalized > 0) && metric > normalized;
}

function jmeterControlPort(status) {
  const match = String(status?.logTail || "").match(
    /Shutdown\/StopTestNow\/HeapDump\/ThreadDump message on port\s+(\d+)/i,
  );
  return match ? Number(match[1]) : 4445;
}

async function stopJmeterByControlPort(jmeterHome, port, cwd) {
  const javaHome = String(process.env.JAVA_HOME || "").trim();
  const java = javaHome
    ? path.join(javaHome, "bin", process.platform === "win32" ? "java.exe" : "java")
    : "java";
  await runCommand(
    java,
    [
      "-cp",
      path.join(jmeterHome, "bin", "ApacheJMeter.jar"),
      "org.apache.jmeter.util.ShutdownClient",
      "StopTestNow",
      String(port),
    ],
    cwd,
  );
  return {
    stopped: true,
    strategy: "jmeter_control_port",
    control_port: port,
    message: `Sent StopTestNow to JMeter control port ${port}.`,
  };
}

async function waitForExecution(
  client,
  executionId,
  timeoutMs,
  workflow,
  outputDir,
  jmeterHome,
) {
  const deadline = Date.now() + timeoutMs;
  const startedAt = Date.now();
  const monitor = autoStopConfiguration(workflow);
  const windows = { error_rate: 0, p95: 0, p99: 0 };
  let nextMonitorAt = startedAt + monitor.grace_period_seconds * 1000;
  let autoStop = {
    configured: monitor.enabled,
    triggered: false,
    reason: "",
    thresholds: {
      max_error_rate_pct: monitor.max_error_rate_pct,
      max_p95_ms: monitor.max_p95_ms,
      max_p99_ms: monitor.max_p99_ms,
    },
    policy: {
      sample_interval_seconds: monitor.sample_interval_seconds,
      grace_period_seconds: monitor.grace_period_seconds,
      min_samples: monitor.min_samples,
      latency_consecutive_windows: monitor.latency_consecutive_windows,
      error_consecutive_windows: monitor.error_consecutive_windows,
      warmup_samples_per_label: monitor.warmup_samples_per_label,
    },
  };
  let status;
  do {
    await new Promise((resolve) => setTimeout(resolve, 500));
    status = await callTool(client, "get_execution_status", { executionId });
    const now = Date.now();
    const elapsedSeconds = Number(((now - startedAt) / 1000).toFixed(1));
    const executionPercent = Math.min(70, 32 + Math.floor(elapsedSeconds / Math.max(timeoutMs / 1000, 1) * 38));
    writeProgress(
      outputDir,
      "jmeter_execution",
      executionPercent,
      "JMeter正在执行性能请求。",
      { execution_id: executionId, elapsed_seconds: elapsedSeconds, execution_status: status.status },
    );
    if (
      status.status === "running"
      && monitor.enabled
      && !autoStop.attempted
      && now >= nextMonitorAt
    ) {
      nextMonitorAt = now + monitor.sample_interval_seconds * 1000;
      try {
        if (!status.aggregateFilename || !existsSync(status.aggregateFilename)) {
          throw new Error("The live aggregate JTL is not available yet.");
        }
        const liveSamples = measuredRequestSamples(
          parseJtl(status.aggregateFilename),
          monitor.warmup_samples_per_label,
        );
        const liveReport = computeAggregate(liveSamples);
        const metrics = monitoredRequestMetrics(liveReport);
        if (metrics.samples >= monitor.min_samples) {
          windows.error_rate = exceeded(
            metrics.error_rate_pct,
            monitor.max_error_rate_pct,
            true,
          ) ? windows.error_rate + 1 : 0;
          windows.p95 = exceeded(metrics.p95_ms, monitor.max_p95_ms)
            ? windows.p95 + 1 : 0;
          windows.p99 = exceeded(metrics.p99_ms, monitor.max_p99_ms)
            ? windows.p99 + 1 : 0;

          const reasons = [];
          if (windows.error_rate >= monitor.error_consecutive_windows) {
            reasons.push(
              `error_rate ${metrics.error_rate_pct}% > ${monitor.max_error_rate_pct}%`,
            );
          }
          if (windows.p95 >= monitor.latency_consecutive_windows) {
            reasons.push(`p95 ${metrics.p95_ms}ms > ${monitor.max_p95_ms}ms`);
          }
          if (windows.p99 >= monitor.latency_consecutive_windows) {
            reasons.push(`p99 ${metrics.p99_ms}ms > ${monitor.max_p99_ms}ms`);
          }
          autoStop = {
            ...autoStop,
            observed_at: new Date().toISOString(),
            elapsed_seconds: Number(((now - startedAt) / 1000).toFixed(1)),
            metrics,
            windows: { ...windows },
            last_monitor_error: "",
          };
          writeFileSync(
            path.join(outputDir, "live-threshold-monitor.json"),
            JSON.stringify(autoStop, null, 2),
            "utf-8",
          );
          if (reasons.length) {
            const mcpStop = await callTool(client, "stop_execution", { executionId });
            let stopped = { ...mcpStop, strategy: "mcp_stop_execution" };
            if (!mcpStop.stopped) {
              try {
                stopped = await stopJmeterByControlPort(
                  jmeterHome,
                  jmeterControlPort(status),
                  outputDir,
                );
                stopped.mcp_stop_result = mcpStop;
              } catch (error) {
                stopped = {
                  stopped: false,
                  strategy: "mcp_then_jmeter_control_port",
                  message: String(error?.message || error),
                  mcp_stop_result: mcpStop,
                };
              }
            }
            autoStop = {
              ...autoStop,
              attempted: true,
              triggered: Boolean(stopped.stopped),
              reason: reasons.join("; "),
              stop_result: stopped,
            };
            writeFileSync(
              path.join(outputDir, "live-threshold-monitor.json"),
              JSON.stringify(autoStop, null, 2),
              "utf-8",
            );
            if (autoStop.triggered) {
              writeProgress(
                outputDir,
                "automatic_stop",
                72,
                `性能阈值已触发，正在停止执行并保留现场：${autoStop.reason}`,
                { execution_id: executionId, elapsed_seconds: autoStop.elapsed_seconds },
              );
            }
          }
        }
      } catch (error) {
        autoStop = {
          ...autoStop,
          last_monitor_error: String(error?.message || error),
        };
      }
    }
    if (Date.now() > deadline) throw new Error(`Execution timed out: ${executionId}`);
  } while (status.status === "running");
  return { ...status, autoStop };
}

async function generateHtml(jmeterHome, jtlPath, htmlDir, reportLog) {
  rmSync(htmlDir, { recursive: true, force: true });
  const jmeterBat = path.join(jmeterHome, "bin", "jmeter.bat");
  const quote = (value) => `'${value.replace(/'/g, "''")}'`;
  const commandLine = `& ${quote(jmeterBat)} -g ${quote(jtlPath)} -o ${quote(htmlDir)} -j ${quote(reportLog)}`;
  return runCommand(
    "powershell.exe",
    ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", commandLine],
    path.dirname(jtlPath),
  );
}

function buildAnalysis(workflow, report, status, artifacts) {
  const autoStop = status.autoStop || { configured: false, triggered: false };
  const checks = {
    execution_completed: status.status === "completed",
    execution_finished: ["completed", "failed"].includes(status.status),
    jtl_created: existsSync(artifacts.jtl),
    html_created: existsSync(artifacts.html_index),
  };
  const artifactsReady = (checks.execution_completed || autoStop.triggered)
    && checks.jtl_created
    && checks.html_created;
  return {
    schema_version: "1.0",
    engine: "jmeter-mcp-server@0.3.1",
    decision: autoStop.triggered ? "AUTO_STOPPED" : artifactsReady ? "EXECUTED" : "FAILED",
    checks,
    auto_stop: autoStop,
    performance_gate_owner: "quality_hub_backend.services.performance_analysis",
    forwarded_thresholds: workflow.thresholds || {},
    metrics: report.overall,
    per_sampler: report.byLabel,
    artifacts,
    limitations: [
      "MCP 0.3.1 does not create the JMeter HTML dashboard, so the bridge invokes JMeter report generation.",
      "MCP 0.3.1 does not accept runtime -J properties during execute_test_plan.",
      "Credentialed plans receive a process-scoped Base64 runtime payload managed by the platform; credentials are not persisted in JMX or workflow files.",
      "The MCP bridge validates execution artifacts only; performance acceptance is evaluated after JTL collection by the platform.",
    ],
  };
}

async function main() {
  const options = readArguments(process.argv.slice(2));
  if (!existsSync(options.workflowPath)) {
    throw new Error(`Workflow not found: ${options.workflowPath}`);
  }
  if (!existsSync(MCP_ENTRY)) {
    throw new Error(`Install MCP dependencies first: npm install --prefix ${ROOT}`);
  }
  if (!existsSync(path.join(options.jmeterHome, "bin", "jmeter.bat"))) {
    throw new Error(`Invalid JMeter home: ${options.jmeterHome}`);
  }
  mkdirSync(options.outputDir, { recursive: true });
  mkdirSync(options.workspace, { recursive: true });
  writeProgress(options.outputDir, "preparing", 22, "正在检查JMeter MCP执行环境。");

  let workflow = JSON.parse(readFileSync(options.workflowPath, "utf-8"));
  ensureNoRawCredentials(workflow);
  let selfTestServer;
  if (options.selfTest) {
    selfTestServer = await startSelfTestServer();
    const selfTestJmx = path.join(options.outputDir, "self-test-source.jmx");
    writeFileSync(selfTestJmx, buildSelfTestJmx(selfTestServer.url), "utf-8");
    workflow = {
      schema_version: "2.0",
      name: "JMeter MCP import self-test",
      source_jmx: selfTestJmx,
      metadata: { preflight_status: "PASS", execution_mode: "import_only" },
      thresholds: workflow.thresholds || {},
    };
  }

  const client = new Client({ name: "autotest-ai-jmeter-mcp", version: "0.1.0" });
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [MCP_ENTRY],
    cwd: ROOT,
    stderr: "pipe",
    env: {
      ...inheritedEnvironment(),
      JMETER_HOME: options.jmeterHome,
      JMETER_MCP_WORKSPACE: options.workspace,
    },
  });
  let mcpStderr = "";
  transport.stderr?.on("data", (chunk) => {
    mcpStderr += chunk.toString();
  });

  try {
    await client.connect(transport);
    writeProgress(options.outputDir, "mcp_connected", 24, "JMeter MCP已连接，正在检查执行能力。");
    const available = await client.listTools();
    const names = new Set(available.tools.map((tool) => tool.name));
    const missing = REQUIRED_TOOLS.filter((name) => !names.has(name));
    if (missing.length) throw new Error(`Missing MCP tools: ${missing.join(", ")}`);

    writeProgress(options.outputDir, "jmx_import", 26, "正在导入并校验已通过门禁的JMX。");
    const plan = await buildPlan(client, workflow, options.projectRoot);
    const serialized = await callTool(client, "get_test_plan_xml", {
      planId: plan.planId,
    });
    const importedJmx = path.join(options.outputDir, "mcp-imported.jmx");
    writeFileSync(importedJmx, serialized.xml, "utf-8");
    writeProgress(options.outputDir, "jmx_ready", 28, "JMX已由MCP加载，准备执行。");

    if (options.generateOnly) {
      const summary = {
        ok: true,
        status: "READY",
        mode: "import_validation_only",
        plan_id: plan.planId,
        mcp_tool_count: available.tools.length,
        imported: Boolean(plan.imported),
        unknown_element_count: plan.unknownElementCount || 0,
        unknown_element_types: plan.unknownElementTypes || [],
        workflow_path: options.workflowPath,
        imported_jmx: importedJmx,
      };
      writeFileSync(
        path.join(options.outputDir, "generation-summary.json"),
        JSON.stringify(summary, null, 2),
        "utf-8",
      );
      writeProgress(options.outputDir, "ready", 85, "JMX导入验证完成。");
      console.log(JSON.stringify(summary, null, 2));
      return;
    }

    writeProgress(options.outputDir, "jmeter_starting", 30, "正在启动JMeter非GUI执行。");
    const execution = await callTool(client, "execute_test_plan", {
      planId: plan.planId,
    });
    const status = await waitForExecution(
      client,
      execution.executionId,
      options.executionTimeoutSeconds * 1000,
      workflow,
      options.outputDir,
      options.jmeterHome,
    );
    writeProgress(
      options.outputDir,
      "jtl_collection",
      74,
      status.autoStop?.triggered ? "执行已自动停止，正在回收JTL和执行日志。" : "JMeter执行结束，正在回收JTL和执行日志。",
      { execution_id: execution.executionId },
    );
    const report = await callTool(client, "get_execution_report", {
      executionId: execution.executionId,
    });
    if (!status.aggregateFilename || !existsSync(status.aggregateFilename)) {
      throw new Error("MCP execution did not produce aggregate-report.jtl");
    }

    const jtl = path.join(options.outputDir, "result.jtl");
    const executedJmx = path.join(options.outputDir, "executed.jmx");
    const jmeterLog = path.join(options.outputDir, "jmeter.log");
    const reportGenerationLog = path.join(options.outputDir, "report-generation.log");
    const htmlDir = path.join(options.outputDir, "jmeter-html");
    copyFileSync(status.aggregateFilename, jtl);
    copyFileSync(status.jmxPath, executedJmx);
    const sourceLog = path.join(path.dirname(status.jmxPath), "jmeter.log");
    if (existsSync(sourceLog)) copyFileSync(sourceLog, jmeterLog);
    writeProgress(options.outputDir, "html_report", 80, "JTL已回收，正在生成JMeter HTML报告。");
    await generateHtml(options.jmeterHome, jtl, htmlDir, reportGenerationLog);
    writeProgress(options.outputDir, "artifact_summary", 86, "HTML报告已生成，正在整理MCP执行摘要。");

    const artifacts = {
      imported_jmx: importedJmx,
      executed_jmx: executedJmx,
      jtl,
      html_index: path.join(htmlDir, "index.html"),
      jmeter_log: jmeterLog,
      report_generation_log: reportGenerationLog,
    };
    const analysis = buildAnalysis(workflow, report, status, artifacts);
    const analysisPath = path.join(options.outputDir, "analysis.json");
    writeFileSync(analysisPath, JSON.stringify(analysis, null, 2), "utf-8");
    const summary = {
      ok: ["EXECUTED", "AUTO_STOPPED"].includes(analysis.decision),
      plan_id: plan.planId,
      execution_id: execution.executionId,
      mcp_tool_count: available.tools.length,
      self_test: options.selfTest,
      analysis,
    };
    writeFileSync(
      path.join(options.outputDir, "run-summary.json"),
      JSON.stringify(summary, null, 2),
      "utf-8",
    );
    writeProgress(options.outputDir, "mcp_completed", 88, "JMeter MCP执行产物已就绪，等待平台诊断。");
    console.log(JSON.stringify(summary, null, 2));
  } catch (error) {
    if (mcpStderr.trim()) console.error(`MCP stderr:\n${mcpStderr.trim()}`);
    throw error;
  } finally {
    await client.close().catch(() => {});
    if (selfTestServer) {
      await new Promise((resolve) => selfTestServer.server.close(resolve));
    }
  }
}

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exitCode = 1;
});
