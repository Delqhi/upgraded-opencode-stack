#!/usr/bin/env node
import path from 'node:path';
import { ensureDir, parseArgs, printResult, resolveAgentRoot, slugFromRoot, writeIfMissing } from './_a2a-lib.mjs';

const args = parseArgs(process.argv.slice(2));
const agentRoot = resolveAgentRoot(args['agent-root']);
const format = args.format || 'json';
const mode = args.mode || 'check';
const slug = slugFromRoot(agentRoot);

const created = [];
const skipped = [];
const manualFollowups = [];

const completeInstallTemplate = [
  '#!/usr/bin/env bash',
  'set -euo pipefail',
  'ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"',
  'mkdir -p "$ROOT/logs" "$ROOT/data"',
  'if [ -f "$ROOT/package-lock.json" ]; then npm --prefix "$ROOT" ci; elif [ -f "$ROOT/package.json" ]; then npm --prefix "$ROOT" install; fi',
  'if [ -f "$ROOT/requirements.txt" ]; then python3 -m pip install -r "$ROOT/requirements.txt"; fi',
  'if [ -f "$ROOT/package.json" ]; then npm --prefix "$ROOT" run build; fi',
  '',
].join('\n');

const assets = [
  [path.join(agentRoot, '.env.example'), `# ${slug} env contract\n# Fill required values before production deploy\n`],
  [path.join(agentRoot, 'runbooks', 'install.md'), '# Install\n\nUse `scripts/complete-install.sh` as the single supported install path.\n'],
  [path.join(agentRoot, 'runbooks', 'launchagent.md'), '# LaunchAgent\n\nRecord install, verify, restart, rollback, and login-cycle survival steps here.\n'],
  [path.join(agentRoot, 'scripts', 'complete-install.sh'), completeInstallTemplate],
];

ensureDir(path.join(agentRoot, 'logs'));
ensureDir(path.join(agentRoot, 'data'));
ensureDir(path.join(agentRoot, 'launchd'));
ensureDir(path.join(agentRoot, 'scripts'));
ensureDir(path.join(agentRoot, 'runbooks'));

for (const [filePath, content] of assets) {
  if (mode === 'apply') {
    if (writeIfMissing(filePath, content)) {
      created.push(filePath.replace(`${agentRoot}/`, ''));
    } else {
      skipped.push(filePath.replace(`${agentRoot}/`, ''));
    }
  } else {
    skipped.push(filePath.replace(`${agentRoot}/`, ''));
  }
}

manualFollowups.push('Review generated complete-install.sh and replace generic install commands with the real agent dependency contract.');

printResult({ ok: true, created, updated: [], skipped, manualFollowups }, format);
