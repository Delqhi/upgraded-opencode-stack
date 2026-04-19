#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

export function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith('--')) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith('--')) {
      args[key] = true;
      continue;
    }
    args[key] = next;
    i += 1;
  }
  return args;
}

export function resolveAgentRoot(agentRoot) {
  if (!agentRoot) {
    throw new Error('missing --agent-root');
  }
  const resolved = path.resolve(agentRoot);
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isDirectory()) {
    throw new Error(`agent root does not exist: ${resolved}`);
  }
  return resolved;
}

export function readText(filePath) {
  return fs.existsSync(filePath) ? fs.readFileSync(filePath, 'utf8') : '';
}

export function readJson(filePath) {
  return JSON.parse(readText(filePath));
}

export function exists(filePath) {
  return fs.existsSync(filePath);
}

export function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

export function writeIfMissing(filePath, content) {
  if (fs.existsSync(filePath)) return false;
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, content);
  return true;
}

export function writeFile(filePath, content) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, content);
}

export function slugFromRoot(agentRoot) {
  return path.basename(agentRoot).replace(/^A2A-SIN-/, '').toLowerCase().replace(/[^a-z0-9]+/g, '-');
}

export function shellQuote(value) {
  return `'${String(value).replace(/'/g, `'"'"'`)}'`;
}

export function run(cmd, args, options = {}) {
  return spawnSync(cmd, args, {
    encoding: 'utf8',
    stdio: options.stdio || 'pipe',
    cwd: options.cwd,
    shell: false,
  });
}

export function walkFiles(rootDir, include = () => true, out = []) {
  for (const entry of fs.readdirSync(rootDir, { withFileTypes: true })) {
    const fullPath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      if (
        ['node_modules', '.git', 'dist', 'build', '.next', '.venv', 'venv', 'logs', 'data'].includes(entry.name) ||
        entry.name.startsWith('chrome_profile')
      ) continue;
      walkFiles(fullPath, include, out);
    } else if (include(fullPath)) {
      out.push(fullPath);
    }
  }
  return out;
}

export function printResult(result, format = 'json') {
  if (format === 'text') {
    process.stdout.write(`${result.ok ? 'OK' : 'FAIL'}\n`);
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}
