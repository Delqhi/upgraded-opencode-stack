# OpenSIN-Code CLI

**The user-facing coding agent CLI.** Repo: [OpenSIN-Code/OpenSIN-Code](https://github.com/OpenSIN-Code/OpenSIN-Code). Latest release: [`v0.1.0-alpha`](https://github.com/OpenSIN-Code/OpenSIN-Code/releases/tag/v0.1.0-alpha).

## What it does

OpenSIN-Code is the coding agent CLI. It runs locally, brings its own browser session, can drive macOS for computer-use tasks, and orchestrates the [Code-Swarm](code-swarm.md) fleet for parallelizable work.

## Capabilities

- **Two operating modes:** SIN-Zeus (orchestrate the full fleet) and SIN-Solo (single-agent assistant for fast edits)
- **Browser automation:** Chromium + Playwright integration, persistent sessions
- **macOS computer-use:** Antigravity-class capability, free and self-hostable
- **MCP 2.0 native:** plugs into Claude Desktop, Cline, or any MCP-aware client
- **VS Code extensions:** `opensin-code-vscode` and `kairos-vscode`
- **bun-only toolchain** for fast installs and zero-overhead workspaces

## Install

```bash
git clone https://github.com/OpenSIN-Code/OpenSIN-Code
cd OpenSIN-Code
bun install
bun run build
./bin/opensin --help
```

Configure your provider:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or any AI Gateway-compatible key
```

## Status

- Core CLI: **shipped in v0.1.0-alpha**
- Browser-Use + macOS Computer-Use: **shipped**
- VS Code extensions: **shipped**
- Self-hosted CI on OCI A1.Flex (zero-billing): **shipped**

## Known gaps for v0.2.0

- npm distribution (`npm i -g opensin-code`) — currently git+bun-build
- Brew tap (`brew install opensin-code`)
- Two large feature branches pending rebase + review:
  - [#1119](https://github.com/OpenSIN-Code/OpenSIN-Code/pull/1119) — monorepo consolidation + sovereign governance + 14 runtime tools
  - [#1120](https://github.com/OpenSIN-Code/OpenSIN-Code/pull/1120) — Multi-Agent Profiles + Hermes Memory + 176 tests

These are real work that needs rebasing onto current `main` before merge.
