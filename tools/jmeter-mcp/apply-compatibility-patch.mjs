import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const target = path.join(
  root,
  "node_modules",
  "jmeter-mcp-server",
  "dist",
  "execution",
  "processManager.js",
);
const autoFlushArgument = '"-Jjmeter.save.saveservice.autoflush=true"';

if (!existsSync(target)) {
  throw new Error(`jmeter-mcp-server runtime was not installed: ${target}`);
}

let source = readFileSync(target, "utf-8");
if (!source.includes(autoFlushArgument)) {
  const original = '"-Jjmeter.save.saveservice.output_format=csv"]';
  const replacement = '"-Jjmeter.save.saveservice.output_format=csv", "-Jjmeter.save.saveservice.autoflush=true"]';
  if (!source.includes(original)) {
    throw new Error(
      "jmeter-mcp-server processManager layout changed; review the compatibility patch before installing.",
    );
  }
  source = source.replace(original, replacement);
  writeFileSync(target, source, "utf-8");
  console.log("Applied JMeter MCP live-JTL autoflush compatibility patch.");
} else {
  console.log("JMeter MCP live-JTL autoflush compatibility patch is already applied.");
}
