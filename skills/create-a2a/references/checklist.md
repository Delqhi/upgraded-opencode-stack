# SIN A2A Agent Checklist

Use this checklist for every new or normalized SIN A2A agent.

## Required metadata

- `slug`
- `name`
- `teamSlug`
- `teamName`
- `teamManager`
- `description`
- `usage`
- `primaryModel`
- `repoUrl`
- `repoVisibility`
- `docsTabUrl`
- `docsTabId`
- `publicPageUrl`
- `landingPageUrl`
- `hfSpaceUrl`
- `cloudflareTunnel`
- `vmServer`

## Required files

- `A2A-CARD.md`
- `AGENTS.md`
- `agent.json`
- `mcp-config.json`
- `package.json`
- `tsconfig.json`
- `Dockerfile`
- `src/runtime.ts`
- `src/mcp-server.ts`
- `src/a2a-http.ts`
- `src/metadata.ts`
- `src/cli.ts`
- `src/index.ts`

For daemon/local-service agents also require:

- `launchd/<agent-label>.plist`
- `scripts/start-<agent>.sh`
- `scripts/healthcheck-<agent>.sh`
- `scripts/restart-<agent>.sh`
- `runbooks/launchagent.md`

For HF VM / deployable agents also require:

- `scripts/complete-install.sh`
- complete dependency manifests + lockfiles (`package-lock.json`, `bun.lock`, `requirements.txt`, `poetry.lock`, etc. as applicable)
- `.env.example` or equivalent env contract
- explicit system dependency list / install notes for CLIs, browser/runtime, OCR/media tools, and sidecars

## Required platform work

- private GitHub repo exists
- canonical team root under `a2a/<team>/A2A-SIN-*`
- dashboard registry entry exists
- team manager is set and ready
- Google Docs tab exists and is synced from `A2A-CARD.md`
- public page exists on `a2a.delqhi.com/agents/<slug>`
- HF Space URL is set or explicitly marked as target-only
- Cloudflare tunnel field is set

## Required commands

```bash
node /Users/jeremy/dev/SIN-Solver/scripts/create-sin-a2a-agent.mjs --spec /abs/path/to/spec.json
node /Users/jeremy/.config/opencode/skills/sin-a2a-agent-forge/scripts/a2a-audit-deps.mjs --agent-root /abs/path/to/agent-root --format text
node /Users/jeremy/.config/opencode/skills/sin-a2a-agent-forge/scripts/a2a-sync-runtime-assets.mjs --agent-root /abs/path/to/agent-root --mode apply --format text
node /Users/jeremy/.config/opencode/skills/sin-a2a-agent-forge/scripts/a2a-preflight.mjs --agent-root /abs/path/to/agent-root --targets deps,install,assets,daemon,hf --format text
cd /Users/jeremy/dev/SIN-Solver && node scripts/sync-a2a-card-tabs.mjs --agent <slug>
cd /Users/jeremy/dev/SIN-Solver && npm run test:a2a:fleet
```

If root docs changed:

```bash
cd /Users/jeremy/dev/SIN-Solver && npm run test:docs:root
```

## Required finish state

- build passes
- `agent.help` works
- `print-card` works
- fleet validator passes
- no legacy symlink used as canonical root

For daemon/local-service agents also require:

- plist validates with `plutil -lint`
- LaunchAgent loads via `launchctl bootstrap`
- logs exist and show clean startup
- healthcheck script passes
- restart/kickstart path works without orphaned processes
- login-cycle survival plan exists in the runbook

## HF VM Consumer Requirements
- `scripts/hf_pull_script.py` present (injected via setup_consumer_auth.sh macro)
- HF VM deployment uses `SUPABASE_URL` & `SUPABASE_SERVICE_ROLE_KEY`
- NO local Chrome profile setups on the HF VM
- NO local temp-mail Token-Refresh-Service setups on the HF VM
- `scripts/complete-install.sh` present and idempotent
- `agent.json` contains control-plane / capability / consumer-auth metadata
- `npm run sync:a2a:control-plane-projection` executed after registry changes

## Complete-install finish state for HF VM / deployable agents

- `bash scripts/complete-install.sh` works from a fresh clone
- no hidden manual install steps are required
- required language deps and system deps are all declared in the repo
- install path creates expected directories / state locations
- post-install smoke check proves the agent starts and answers health/help
