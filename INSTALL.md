# Upgraded OpenCode Stack

Complete custom enhancement stack for OpenCode CLI. Clone this repo, run install, and your OpenCode CLI is fully upgraded.

## Quick Start

```bash
git clone https://github.com/Delqhi/upgraded-opencode-stack.git
cd upgraded-opencode-stack
./install.sh
```

## What This Installs

| Category         | Count | Description                                                                                                             |
| ---------------- | ----- | ----------------------------------------------------------------------------------------------------------------------- |
| **Skills**       | 45    | Custom workflows for A2A creation, deployment, debugging, browser automation, media analysis, and thumbnail A/B testing |
| **Plugins**      | 3     | Auth plugins for Antigravity and OpenRouter                                                                             |
| **Agents**       | 21    | Custom agents including SIN-Zeus, OMOC swarm, and multimodal tools                                                      |
| **Commands**     | 14    | Custom CLI commands for swarm orchestration, terminal management, Zeus control, video analysis                          |
| **Scripts**      | 13    | Utility scripts for sync, rotation, PR watching, GitHub management, video analysis                                      |
| **CLI Tools**    | 12    | sin-\* CLI tools for docs, n8n, telegram, health, metrics                                                               |
| **Templates**    | 5     | JSON schemas for work items, PR watchers, governance                                                                    |
| **Hooks**        | 1     | Pre-commit hook for auto-sync                                                                                           |
| **Instructions** | 4     | Orchestrator, planner, worker guidelines                                                                                |
| **Rules**        | 1     | Model preservation rules                                                                                                |

## Prerequisites

- macOS (Apple Silicon or Intel)
- Node.js 20+ (`brew install node`)
- OpenCode CLI installed
- Git configured with GitHub access
- npm/pnpm for plugin installation

## Directory Structure

```
upgraded-opencode-stack/
├── install.sh              # Main installer
├── opencode.json           # OpenCode configuration (sanitized)
├── AGENTS.md               # Global agent rules
├── skills/                 # 29 custom skills
├── plugins/                # Custom auth plugins
│   └── local-plugins/      # Local plugin source
├── commands/               # 13 custom commands
├── scripts/                # 12 utility scripts
├── hooks/                  # Git hooks
├── templates/              # JSON schemas
├── instructions/           # Agent instructions
├── rules/                  # Model rules
├── tools/                  # Utility tools
├── platforms/              # Platform evidence
├── bin/                    # CLI tool stubs
└── docs/                   # Documentation
```

## Post-Install Steps

1. Set environment variables (see `.env.example`)
2. Configure auth plugins with your credentials
3. Run `sin-sync` to sync to other machines
4. Verify with `opencode --version` and test a skill

### Video Analysis

Use `/video-check <video-path> [custom-prompt]` for token-efficient video summaries powered by `nvidia/meta/llama-3.2-11b-vision-instruct`.
