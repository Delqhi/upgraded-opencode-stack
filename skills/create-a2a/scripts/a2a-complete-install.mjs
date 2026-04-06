#!/usr/bin/env node
import path from 'node:path';
import { parseArgs, printResult, resolveAgentRoot, exists, run } from './_a2a-lib.mjs';

const args = parseArgs(process.argv.slice(2));
const agentRoot = resolveAgentRoot(args['agent-root']);
const format = args.format || 'json';
const mode = args.mode || 'plan';
const includeBuild = String(args['include-build'] || 'true') !== 'false';

const commands = [];
const failures = [];
const installedRoots = [];
let packageManager = 'none';

if (exists(path.join(agentRoot, 'package.json'))) {
  if (exists(path.join(agentRoot, 'bun.lock')) || exists(path.join(agentRoot, 'bun.lockb'))) {
    packageManager = 'bun';
    commands.push(['bun', ['install']]);
  } else if (exists(path.join(agentRoot, 'pnpm-lock.yaml'))) {
    packageManager = 'pnpm';
    commands.push(['pnpm', ['install', '--frozen-lockfile']]);
  } else if (exists(path.join(agentRoot, 'package-lock.json'))) {
    packageManager = 'npm';
    commands.push(['npm', ['ci']]);
  } else {
    failures.push('package.json exists but no lockfile was found');
  }
}

if (exists(path.join(agentRoot, 'requirements.txt'))) {
  commands.push(['python3', ['-m', 'pip', 'install', '-r', 'requirements.txt']]);
}

if (exists(path.join(agentRoot, 'pyproject.toml')) && !exists(path.join(agentRoot, 'requirements.txt'))) {
  commands.push(['python3', ['-m', 'pip', 'install', '-e', '.']]);
}

if (includeBuild && exists(path.join(agentRoot, 'package.json'))) {
  commands.push(['npm', ['run', 'build']]);
}

if (mode === 'apply') {
  for (const [cmd, cmdArgs] of commands) {
    const result = run(cmd, cmdArgs, { cwd: agentRoot });
    if (result.status !== 0) {
      failures.push(`${cmd} ${cmdArgs.join(' ')} failed: ${result.stderr || result.stdout}`);
      break;
    }
    installedRoots.push(agentRoot);
  }
}

printResult(
  {
    ok: failures.length === 0,
    installedRoots,
    packageManager,
    mode,
    checks: {
      lockfilePresent: packageManager !== 'none' || !exists(path.join(agentRoot, 'package.json')),
      nodeModulesPresent: exists(path.join(agentRoot, 'node_modules')),
      runtimeDepsResolved: failures.length === 0,
      buildSucceeded: !includeBuild || exists(path.join(agentRoot, 'dist')) || failures.length === 0,
    },
    plannedCommands: commands.map(([cmd, cmdArgs]) => `${cmd} ${cmdArgs.join(' ')}`),
    failures,
  },
  format,
);
