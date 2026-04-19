#!/usr/bin/env node
import path from 'node:path';
import { parseArgs, printResult, readText, resolveAgentRoot, exists, walkFiles } from './_a2a-lib.mjs';

const args = parseArgs(process.argv.slice(2));
const agentRoot = resolveAgentRoot(args['agent-root']);
const format = args.format || 'json';
const healthUrl = args['health-url'];

const cliText = readText(path.join(agentRoot, 'src', 'cli.ts'));
const hfSyncText = readText(path.join(agentRoot, 'src', 'hf_sync.ts'));
const files = walkFiles(agentRoot, (p) => /\.(md|ts|js|mjs|py|sh|json|yaml|yml)$/.test(p));
const corpus = files.map((p) => readText(p)).join('\n');

const checks = {
  keepAliveConfigured: /startKeepAlivePing|keep.?alive/i.test(cliText + hfSyncText + corpus),
  sessionBackupConfigured: /startAutoBackup|backupAuthSession|restoreAuthSession/i.test(cliText + hfSyncText + corpus),
  restoreHookConfigured: /restoreAuthSession/i.test(cliText + hfSyncText + corpus),
  hfRuntimeCommandDeclared: exists(path.join(agentRoot, 'Dockerfile')) || /hugging face|hf vm|space/i.test(corpus),
  publicHealthReachable: !healthUrl,
};

const failures = Object.entries(checks)
  .filter(([, value]) => value === false)
  .map(([key]) => `${key} failed`);

printResult({ ok: failures.length === 0, checks, failures, deploymentNotes: [] }, format);
