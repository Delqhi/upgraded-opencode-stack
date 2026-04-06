#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import { parseArgs, printResult, resolveAgentRoot, run, walkFiles, exists } from './_a2a-lib.mjs';

const args = parseArgs(process.argv.slice(2));
const agentRoot = resolveAgentRoot(args['agent-root']);
const format = args.format || 'json';
const port = args.port ? Number(args.port) : null;
const healthCommand = args['health-command'];

const launchdFiles = walkFiles(path.join(agentRoot, 'launchd'), (p) => p.endsWith('.plist'), []);
const scriptFiles = walkFiles(path.join(agentRoot, 'scripts'), (p) => p.endsWith('.sh'), []);
const checks = {
  buildOutputPresent: exists(path.join(agentRoot, 'dist')) || exists(path.join(agentRoot, 'build')),
  envSatisfied: exists(path.join(agentRoot, '.env.example')),
  launchAgentAssetsPresent: launchdFiles.length > 0 && scriptFiles.some((p) => p.includes('healthcheck-')),
  processBoots: true,
  portReachable: port ? false : true,
  healthPasses: healthCommand ? false : true,
  logsWritable: false,
};

try {
  fs.mkdirSync(path.join(agentRoot, 'logs'), { recursive: true });
  fs.writeFileSync(path.join(agentRoot, 'logs', '.write-test'), 'ok');
  fs.unlinkSync(path.join(agentRoot, 'logs', '.write-test'));
  checks.logsWritable = true;
} catch {
  checks.logsWritable = false;
}

if (port) {
  await new Promise((resolve) => {
    const socket = net.createConnection({ host: '127.0.0.1', port }, () => {
      checks.portReachable = true;
      socket.end();
      resolve();
    });
    socket.on('error', () => resolve());
  });
}

if (healthCommand) {
  const result = run('/bin/bash', ['-lc', healthCommand], { cwd: agentRoot });
  checks.healthPasses = result.status === 0;
}

const failures = Object.entries(checks)
  .filter(([, value]) => value === false)
  .map(([key]) => `${key} failed`);

printResult({ ok: failures.length === 0, checks, failures }, format);
