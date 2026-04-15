# Upgraded OpenCode Stack

> **1:1 Kopie** deines kompletten custom OpenCode CLI Setups. Klonen, installieren, fertig — identisch auf jedem MacBook.

## Quick Start

```bash
git clone https://github.com/Delqhi/upgraded-opencode-stack.git
cd upgraded-opencode-stack
./install.sh
```

Das war's. Danach `.env` mit deinen API Keys befüllen und du hast **exakt dasselbe OpenCode** wie auf deinem Haupt-Mac.

## Was wird installiert

| Kategorie | Anzahl | Zielverzeichnis |
|-----------|--------|-----------------|
| **Skills** | 44 | `~/.config/opencode/skills/` |
| **Plugins** | 4 | Global via npm + `~/.config/opencode/plugins/` |
| **Agents** | 21 | `~/.config/opencode/agents/` |
| **Agent Instructions** | 37 | `~/.config/opencode/agents-instructions/` |
| **Commands** | 13 | `~/.config/opencode/commands/` |
| **Scripts** | 17 | `~/.config/opencode/scripts/` |
| **CLI Tools** | 11 | `~/.local/bin/` |
| **Templates** | 5 | `~/.config/opencode/templates/` |
| **Hooks** | 1 | `~/.config/opencode/hooks/` |
| **Instructions** | 4 | `~/.config/opencode/instructions/` |
| **Rules** | 1 | `~/.config/opencode/rules/` |
| **Tools** | 1 | `~/.config/opencode/tools/` |
| **Vendor** | 1633 | `~/.config/opencode/vendor/` |
| **Backups** | 52 | `~/.config/opencode/backups/` |
| **Config** | 1 | `~/.config/opencode/opencode.json` (intelligent gemerged) |

## Skills (44)

| Skill | Zweck |
|-------|-------|
| `create-a2a` | A2A Agent erstellen |
| `create-a2a-mcp` | A2A MCP Server erstellen |
| `create-a2a-sin-coder` | A2A Coder Agent bootstrappen |
| `create-a2a-team` | SIN A2A Team Manager erstellen |
| `create-auth-plugin` | OpenCode Auth Plugin bauen |
| `create-telegrambot` | Telegram Bot erstellen/deployen |
| `create-github-account` | GitHub Account erstellen |
| `create-github-app` | GitHub App erstellen |
| `create-hf-space-vm` | HuggingFace Space VM erstellen |
| `cloudflare-deploy` | Cloudflare Deployment |
| `vercel-deploy` | Vercel Deployment |
| `sin-bridge` | OpenSIN Bridge Chrome Extension |
| `sin-vision-colab` | Screen Recording + AI Vision |
| `enterprise-deep-debug` | Enterprise Debugging |
| `omoc-plan-swarm` | OMOC Plan Swarm |
| `check-plan-done` | Plan-and-Execute Workflow |
| `self-healer` | Self-Healing |
| `sovereign-repo-governance` | Repo Governance |
| `sovereign-research` | Sovereign Research |
| `opencode-subagent-delegation` | Codex ↔ OpenCode Orchestration |
| `anonymous` | Browser Automation (webauto-nodriver-mcp) |
| `browser-crashtest-lab` | Full-Browser Crash-Test + QA |
| `doc` | .docx Dokumenten-Handling |
| `pdf` | PDF Handling |
| `imagegen` | Bild-Generierung via Gemini |
| `gen-thumbnail` | Self-learning YouTube Thumbnail A/B Engine |
| `nvidia-3d-forge` | 3D Asset Pipeline |
| `nvidia-video-forge` | Video-Generierung via NVIDIA |
| `sora` | Sora Video-Generierung |

## Plugins (4)

| Plugin | Zweck |
|--------|-------|
| `opencode-antigravity-auth` | Antigravity OAuth — Token-Rotation für Claude/Gemini |
| `oh-my-opencode` | Oh-My-OpenCode Framework — Commands, Hooks, Orchestration |
| `opencode-qwen-auth` | Qwen OAuth Auth via `/connect` |
| `opencode-openrouter-auth` | OpenRouter Auth mit lokalem Proxy (local source included) |

## CLI Tools (11)

| Tool | Zweck |
|------|-------|
| `sin-document-forge` | Word-Dokumente generieren |
| `sin-google-docs` | Google Docs MCP |
| `sin-health` | System Health Check |
| `sin-metrics` | Metriken sammeln |
| `sin-n8n` | n8n Workflow Management |
| `sin-pull-token` | Token Pull |
| `sin-rotate` | Token Rotation |
| `sin-rotator` | Token Rotator |
| `sin-sync` | OpenCode Config Sync (Mac → OCI VM) |
| `sin-telegrambot` | Telegram Bot CLI |
| `check-should-automate` | Inefficiency Detector für n8n |

## Provider (5 konfiguriert)

| Provider | Modelle |
|----------|---------|
| **google** (Antigravity) | `antigravity-claude-sonnet-4-6`, `antigravity-claude-opus-4-6-thinking`, `antigravity-gemini-3.1-pro`, `antigravity-gemini-3-flash` |
| **nvidia-nim** | `qwen-3.5-122b`, `qwen-3.5-397b` |
| **openai** | `gpt-5.4` |
| **openrouter** | 7 Free-Modelle (DeepSeek, Gemini, Llama, Phi) |
| **qwen-code** | Qwen 3.6 Plus, Qwen 3.6 Vision Plus (OAuth, free up to 2000/day) |

## Commands (13)

| Command | Zweck |
|---------|-------|
| `omoc-swarm-create` | Swarm erstellen/registrieren |
| `omoc-swarm-discover` | Swarm aus Session-Titeln entdecken |
| `omoc-jam` | Collaborative Swarm Jam |
| `omoc-max` | OMOC MAX best-of-n |
| `omoc-status` | Swarm Members anzeigen |
| `omoc-autostart` | Auto-bind Swarm + JAM Guidance |
| `sin-terminal-orchestrate` | SIN-Terminal — parallele Sessions steuern |
| `sin-terminal-orchestrate-status` | Terminal Orchestration Status |
| `sin-terminal-orchestrate-delegate` | Follow-up Prompt delegieren |
| `sin-terminal-orchestrate-stop` | Alle Sessions stoppen |
| `sin-zeus-bootstrap` | GitHub Project + Issue Pool aus Zeus Plan |
| `sin-zeus-hermes` | Hermes Dispatch Payloads generieren |
| `sin-zeus-status` | Zeus Control-Plane Status |

## Vanilla OpenCode vs. Oh-My-OpenCode vs. Dein Custom Stack

### Was OpenCode nativ kann (ohne Plugins)

| Feature | Vanilla OpenCode |
|---------|-----------------|
| Agent Management | ✅ `opencode agent create/list` |
| Session Export/Import | ✅ `opencode export/import` |
| LSP Tools | ✅ Integriert |
| MCP Management | ✅ `opencode mcp` |
| Hooks | ✅ Eigenes Hook-System |
| Plugins | ✅ `opencode plugin` |
| GitHub Integration | ✅ `opencode github`, `opencode pr` |
| Subagent Delegation | ✅ `task()` Tool |
| Ralph/Ultrawork Loop | ✅ `/ulw-loop`, `/ralph-loop` |
| Provider-Config | ✅ `opencode providers` |
| Model-Listing | ✅ `opencode models` |
| Token Stats | ✅ `opencode stats` |

### Was Oh-My-OpenCode (OMO) zusätzlich bringt

| Feature | OMO | Vanilla |
|---------|-----|---------|
| **Curated Agent-Teams** (Oracle, Librarian, Explore, Sisyphus) | ✅ Vorkonfiguriert | ❌ Manuell |
| **Sisyphus Ultraworker** | ✅ Endlos-Schleife bis Task fertig | ❌ |
| **Todo Continuation Enforcer** | ✅ Zwingt Agent weiterzuarbeiten | ❌ |
| **Comment Checker** | ❌ DEAKTIVIERT — Kommentare sind PFLICHT! | ✅ |
| **Curated MCPs** (Exa, Context7, Grep.app) | ✅ Vorkonfiguriert | ❌ |
| **Google OAuth Auth** | ✅ Eingebaut | ❌ |
| **Claude Code Compatibility** | ✅ Commands, Agents, Skills, Hooks | ❌ |
| **Tmux Integration** | ✅ | ❌ |
| **JSONC Config Support** | ✅ | ❌ |

### Was NUR dein Custom Stack hat (nicht in OMO!)

| Feature | Dein Stack | OMO |
|---------|-----------|-----|
| **OMOC Swarm** (Atlas, Hephaestus, Metis, Momus, Prometheus) | ✅ 5-Agenten-Schwarm | ❌ Nur Sisyphus |
| **SIN-Zeus** (Fleet Commander) | ✅ | ❌ |
| **SIN-Terminal Orchestration** | ✅ 4 Commands | ❌ |
| **44 Custom Skills** | ✅ | ❌ (hat 0) |
| **Antigravity Auth Plugin** | ✅ Token-Rotation | ❌ (eigenes Google Auth) |
| **OpenRouter Auth (lokal)** | ✅ Mit Proxy | ❌ |
| **11 sin-* CLI Tools** | ✅ | ❌ |
| **17 Scripts** (Sync, Rotation, PR-Watcher, etc.) | ✅ | ❌ |
| **n8n Integration** | ✅ sin-n8n CLI | ❌ |
| **Telegram Bot Integration** | ✅ | ❌ |
| **Agent Instructions** (37 Dateien) | ✅ | ❌ |
| **Vendor Dependencies** | ✅ 1633 Dateien | ❌ |
| **sin-sync** (Mac → OCI VM) | ✅ | ❌ |

## Post-Install

```bash
# 1. API Keys setzen
cp .env.example .env
# .env bearbeiten und deine Keys eintragen

# 2. Verifizieren
opencode --version
ls ~/.config/opencode/skills/ | wc -l  # Sollte 44+ zeigen

# 3. Sync zu OCI VM (optional)
sin-sync
```

## .env Variablen

```bash
NVIDIA_API_KEY=          # NVIDIA NIM
GOOGLE_API_KEY=          # Gemini Direct API
OPENROUTER_API_KEY=      # OpenRouter
OPENAI_API_KEY=          # OpenAI (via Proxy)
TELEGRAM_BOT_TOKEN=      # sin-telegrambot
N8N_BASE_URL=            # n8n URL
N8N_API_KEY=             # n8n API Key
OCI_VM_HOST=             # OCI VM Host (sin-sync)
OCI_VM_USER=             # OCI VM User
SUPABASE_URL=            # Supabase
SUPABASE_KEY=            # Supabase Key
```

## Repo Struktur

```
upgraded-opencode-stack/
├── install.sh              # Haupt-Installer
├── opencode.json           # OpenCode Config (gesanitized)
├── AGENTS.md               # Globale Agent-Regeln
├── .env.example            # API Key Template
├── bin/                    # 11 echte CLI Tools
├── skills/                 # 44 Skills
├── plugins/                # 4 Plugins (1 lokal)
├── agents/                 # Agent-Definitionen
├── agents-instructions/    # 37 Agent-Instruktionen
├── commands/               # 12 Custom Commands
├── scripts/                # 17 Scripts
├── hooks/                  # Git Hooks
├── templates/              # JSON Schemas
├── instructions/           # 4 Anleitungen
├── rules/                  # Model-Regeln
├── tools/                  # Utility Tools
├── platforms/              # Platform Evidence
├── vendor/                 # Vendored Dependencies
├── backups/                # Config Backups
└── docs/                   # Dokumentation
```

## Was NICHT im Repo ist (aus Sicherheitsgründen)

- `antigravity-accounts.json` — OAuth Tokens
- `token.json`, `auth.json` — API Keys
- `telegram_config.json` — Telegram Config
- `*_cookies.json` — Browser Cookies
- `*.db`, `*.db-wal` — Lokale Datenbanken
- `node_modules/` — Wird per `npm install -g` installiert

Diese Dateien werden vom Installer als Platzhalter angelegt und müssen manuell befüllt werden.

---

**Built by OpenSIN-AI Fleet** — sincode
