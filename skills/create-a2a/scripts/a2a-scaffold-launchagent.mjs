#!/usr/bin/env node
import path from 'node:path';
import { parseArgs, printResult, resolveAgentRoot, shellQuote, slugFromRoot, writeFile } from './_a2a-lib.mjs';

const args = parseArgs(process.argv.slice(2));
const agentRoot = resolveAgentRoot(args['agent-root']);
const format = args.format || 'json';
const slug = args.slug || slugFromRoot(agentRoot);
const label = args.label || `com.sin.${slug}`;
const command = args.command || 'npm run start';
const workingDir = args['working-dir'] || agentRoot;
const startScript = path.join(agentRoot, 'scripts', `start-${slug}.sh`);
const healthScript = path.join(agentRoot, 'scripts', `healthcheck-${slug}.sh`);
const restartScript = path.join(agentRoot, 'scripts', `restart-${slug}.sh`);
const plistPath = path.join(agentRoot, 'launchd', `${label}.plist`);
const runbookPath = path.join(agentRoot, 'runbooks', 'launchagent.md');

writeFile(
  startScript,
  `#!/usr/bin/env bash\nset -euo pipefail\nROOT=${shellQuote(agentRoot)}\ncd ${shellQuote(workingDir)}\nmkdir -p "$ROOT/logs" "$ROOT/data"\nexec /bin/bash -lc ${shellQuote(command)}\n`,
);
writeFile(
  healthScript,
  `#!/usr/bin/env bash\nset -euo pipefail\nROOT=${shellQuote(agentRoot)}\n[ -d "$ROOT/logs" ] || { echo 'logs missing'; exit 1; }\necho 'healthcheck placeholder: replace with real health command'\n`,
);
writeFile(
  restartScript,
  `#!/usr/bin/env bash\nset -euo pipefail\nPLIST=\"$HOME/Library/LaunchAgents/${label}.plist\"\nlaunchctl bootout gui/$(id -u) \"$PLIST\" 2>/dev/null || true\nlaunchctl bootstrap gui/$(id -u) \"$PLIST\"\nlaunchctl kickstart -k gui/$(id -u)/${label}\n`,
);
writeFile(
  plistPath,
  `<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0">\n  <dict>\n    <key>Label</key>\n    <string>${label}</string>\n    <key>ProgramArguments</key>\n    <array>\n      <string>/bin/bash</string>\n      <string>${startScript}</string>\n    </array>\n    <key>WorkingDirectory</key>\n    <string>${workingDir}</string>\n    <key>RunAtLoad</key>\n    <true/>\n    <key>KeepAlive</key>\n    <true/>\n    <key>StandardOutPath</key>\n    <string>${agentRoot}/logs/${slug}.launchagent.out.log</string>\n    <key>StandardErrorPath</key>\n    <string>${agentRoot}/logs/${slug}.launchagent.err.log</string>\n  </dict>\n</plist>\n`,
);
writeFile(
  runbookPath,
  `# LaunchAgent\n\nLabel: \`${label}\`\n\n## Install\n\nCopy \`${path.basename(plistPath)}\` to \`~/Library/LaunchAgents/\` and bootstrap it with \`launchctl\`.\n\n## Verify\n\n- \`plutil -lint ${plistPath}\`\n- \`launchctl list | grep ${slug}\`\n- run \`${path.basename(healthScript)}\`\n\n## Restart\n\nUse \`${path.basename(restartScript)}\` only.\n`,
);

printResult(
  {
    ok: true,
    plistPath,
    wrapperPath: startScript,
    logPaths: {
      stdout: `${agentRoot}/logs/${slug}.launchagent.out.log`,
      stderr: `${agentRoot}/logs/${slug}.launchagent.err.log`,
    },
    nextCommands: [
      `chmod +x ${startScript} ${healthScript} ${restartScript}`,
      `plutil -lint ${plistPath}`,
    ],
  },
  format,
);
