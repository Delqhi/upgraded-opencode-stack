#!/usr/bin/env node
import path from 'node:path';
import { parseArgs, printResult, readText, resolveAgentRoot, walkFiles, exists } from './_a2a-lib.mjs';

const args = parseArgs(process.argv.slice(2));
const agentRoot = resolveAgentRoot(args['agent-root']);
const format = args.format || 'json';

const pkg = path.join(agentRoot, 'package.json');
const pkgLock = path.join(agentRoot, 'package-lock.json');
const bunLock = path.join(agentRoot, 'bun.lock');
const bunLockb = path.join(agentRoot, 'bun.lockb');
const pnpmLock = path.join(agentRoot, 'pnpm-lock.yaml');
const reqTxt = path.join(agentRoot, 'requirements.txt');
const pyproject = path.join(agentRoot, 'pyproject.toml');
const poetryLock = path.join(agentRoot, 'poetry.lock');
const completeInstall = path.join(agentRoot, 'scripts', 'complete-install.sh');
const envExample = path.join(agentRoot, '.env.example');

const drift = [];

if (exists(pkg) && !exists(pkgLock) && !exists(bunLock) && !exists(bunLockb) && !exists(pnpmLock)) {
  drift.push({
    type: 'lockfile-mismatch',
    severity: 'error',
    file: 'package.json',
    detail: 'JavaScript package manifest exists without a tracked lockfile.',
    suggestedFix: 'Add package-lock.json, bun.lock/bun.lockb, or pnpm-lock.yaml and use it in install scripts.',
  });
}

if (exists(pyproject) && !exists(poetryLock) && !exists(reqTxt)) {
  drift.push({
    type: 'lockfile-mismatch',
    severity: 'warn',
    file: 'pyproject.toml',
    detail: 'Python project file exists without poetry.lock or requirements.txt fallback.',
    suggestedFix: 'Track poetry.lock or a requirements export for reproducible installs.',
  });
}

if (!exists(completeInstall)) {
  drift.push({
    type: 'asset-drift',
    severity: 'error',
    file: 'scripts/complete-install.sh',
    detail: 'complete-install script is missing.',
    suggestedFix: 'Generate it with a2a-sync-runtime-assets.mjs or add it manually.',
  });
}

if (!exists(envExample)) {
  drift.push({
    type: 'asset-drift',
    severity: 'warn',
    file: '.env.example',
    detail: 'Env contract file is missing.',
    suggestedFix: 'Add .env.example with all required runtime variables.',
  });
}

const toolPatterns = {
  ffmpeg: /\bffmpeg\b/g,
  tesseract: /\btesseract\b/g,
  'google-chrome': /\bgoogle-chrome\b/g,
  Xvfb: /\bXvfb\b/g,
  cloudflared: /\bcloudflared\b/g,
  docker: /\bdocker\b/g,
  gcloud: /\bgcloud\b/g,
  rclone: /\brclone\b/g,
  gh: /\bgh\b/g,
};

const files = walkFiles(agentRoot, (filePath) => /\.(ts|js|mjs|py|sh|md|json|toml|ya?ml)$/.test(filePath));
const corpus = files.map((filePath) => ({ filePath, text: readText(filePath) }));
const completeText = readText(completeInstall) + '\n' + readText(path.join(agentRoot, 'README.md')) + '\n' + readText(envExample);

for (const [tool, pattern] of Object.entries(toolPatterns)) {
  const matches = corpus.filter((entry) => pattern.test(entry.text));
  if (!matches.length) continue;
  if (!pattern.test(completeText)) {
    drift.push({
      type: 'missing-dep',
      severity: 'warn',
      file: matches[0].filePath.replace(`${agentRoot}/`, ''),
      detail: `Runtime appears to reference ${tool}, but complete-install/README/.env.example do not mention it.`,
      suggestedFix: `Declare ${tool} in complete-install.sh or install/runbook docs.`,
    });
  }
}

printResult({ ok: !drift.some((item) => item.severity === 'error'), drift }, format);
