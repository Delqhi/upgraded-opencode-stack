#!/usr/bin/env node
import path from 'node:path';
import { parseArgs, printResult, resolveAgentRoot, run } from './_a2a-lib.mjs';

const args = parseArgs(process.argv.slice(2));
const agentRoot = resolveAgentRoot(args['agent-root']);
const format = args.format || 'json';
const targets = String(args.targets || 'deps,install,assets,daemon,hf').split(',').map((v) => v.trim()).filter(Boolean);
const fixSafeDrift = Boolean(args['fix-safe-drift']);

const scriptDir = path.dirname(new URL(import.meta.url).pathname);
const stages = {
  deps: ['node', [path.join(scriptDir, 'a2a-audit-deps.mjs'), '--agent-root', agentRoot, '--format', 'json']],
  install: ['node', [path.join(scriptDir, 'a2a-complete-install.mjs'), '--agent-root', agentRoot, '--format', 'json', '--mode', fixSafeDrift ? 'apply' : 'plan']],
  assets: ['node', [path.join(scriptDir, 'a2a-sync-runtime-assets.mjs'), '--agent-root', agentRoot, '--format', 'json', '--mode', fixSafeDrift ? 'apply' : 'check']],
  daemon: ['node', [path.join(scriptDir, 'a2a-verify-daemon-readiness.mjs'), '--agent-root', agentRoot, '--format', 'json']],
  hf: ['node', [path.join(scriptDir, 'a2a-verify-hf-vm-readiness.mjs'), '--agent-root', agentRoot, '--format', 'json']],
};

const stageResults = {};
const blockingIssues = [];
for (const target of targets) {
  const stage = stages[target];
  if (!stage) {
    stageResults[target] = 'skip';
    continue;
  }
  const [cmd, cmdArgs] = stage;
  const result = run(cmd, cmdArgs, { cwd: agentRoot });
  if (result.status !== 0) {
    stageResults[target] = 'fail';
    blockingIssues.push(`${target}: ${result.stderr || result.stdout}`);
    continue;
  }
  const payload = JSON.parse(result.stdout || '{}');
  stageResults[target] = payload.ok ? 'pass' : 'fail';
  if (!payload.ok) {
    blockingIssues.push(`${target}: ${JSON.stringify(payload.failures || payload.drift || [])}`);
  }
}

printResult(
  {
    ok: blockingIssues.length === 0,
    stageResults,
    blockingIssues,
    recommendedNextStep: blockingIssues.length ? 'Resolve blocking issues, then rerun a2a-preflight.mjs.' : 'Agent passes current forge preflight gates.',
  },
  format,
);
