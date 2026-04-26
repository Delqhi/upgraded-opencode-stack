import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";

const DEV_ROOT = path.join(os.homedir(), "dev");
const GLOBAL_CONFIG_PATH = path.join(os.homedir(), ".config", "opencode", "opencode.json");
const SKIP_DIRS = new Set([
  ".git",
  "node_modules",
  ".next",
  "dist",
  "build",
  "coverage",
  "vendor",
  "archive",
  "tmp",
  "temp",
]);
const SKIP_PATH_SNIPPETS = [
  `${path.sep}packages${path.sep}ui${path.sep}src${path.sep}theme${path.sep}themes${path.sep}`,
  `${path.sep}packages${path.sep}opencode${path.sep}src${path.sep}cli${path.sep}cmd${path.sep}tui${path.sep}context${path.sep}theme${path.sep}`,
  `${path.sep}go${path.sep}pkg${path.sep}mod${path.sep}`,
];

function stripJsonComments(source) {
  return source
    .split(/\r?\n/)
    .filter((line) => !line.trimStart().startsWith("//"))
    .join("\n")
    .replace(/,\s*([}\]])/g, "$1");
}

async function readJson(filePath) {
  const raw = await fs.readFile(filePath, "utf8");
  return JSON.parse(stripJsonComments(raw));
}

async function walkForConfigs(dir, acc = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (SKIP_DIRS.has(entry.name)) continue;
    const fullPath = path.join(dir, entry.name);
    if (SKIP_PATH_SNIPPETS.some((snippet) => fullPath.includes(snippet))) continue;
    if (entry.isDirectory()) {
      await walkForConfigs(fullPath, acc);
      continue;
    }
    if (entry.isFile() && entry.name === "opencode.json") {
      acc.push(fullPath);
    }
  }
  return acc;
}

function syncConfig(target, globalConfig) {
  const next = { ...target };
  next.plugin = [...(globalConfig.plugin || [])];
  next.model = globalConfig.model;
  next.provider = { ...(next.provider || {}) };
  if (globalConfig.provider?.openai) {
    next.provider.openai = JSON.parse(JSON.stringify(globalConfig.provider.openai));
  }
  return next;
}

const globalConfig = await readJson(GLOBAL_CONFIG_PATH);
const configs = (await walkForConfigs(DEV_ROOT)).filter((filePath) => filePath !== GLOBAL_CONFIG_PATH);
const touched = [];

for (const filePath of configs) {
  const current = await readJson(filePath);
  const next = syncConfig(current, globalConfig);
  if (JSON.stringify(current) === JSON.stringify(next)) continue;
  await fs.writeFile(filePath, `${JSON.stringify(next, null, 2)}\n`);
  touched.push(filePath);
}

for (const filePath of touched) {
  console.log(filePath);
}

console.log(`Synced ${touched.length} local opencode.json file(s).`);
