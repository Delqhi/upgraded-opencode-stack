# Code-Swarm: SOTA Agent Swarm Architecture

> **KEIN tmux! KEINE Worktrees! KEIN Background-Dispatch!**
> Subagent-Delegation erfolgt NUR via opencode-native oh-my-opencode Sub-Sessions.

## 🤖 Main Agents

### SIN-Zeus — Supreme Fleet Commander
| Property | Value |
|----------|-------|
| Model | `fireworks-ai/minimax-m2.7` |
| Role | Fleet Commander |
| Mode | Primary |
| Reasoning | xhigh |

**Capabilities:**
- github-orchestration
- fleet-dispatch
- multi-agent-coordination
- planning
- research

**Hard Rules:**
- NEVER_IDLE_FLEET
- NEVER_DIRECT_CODING
- GITHUB_IS_SOURCE_OF_TRUTH
- MIN_2_PARALLEL_TOOLS

### SIN-Solo — Direct Single-Agent Executor (formerly Sin-Executor-Solo)
| Property | Value |
|----------|-------|
| Model | `vercel/deepseek-v4-pro` |
| Role | Direct Executor |
| Mode | Primary |

**Capabilities:**
- direct-coding
- single-agent-execution
- no-delegation
- minimal-invasive-changes

**Hard Rules:**
- WORK_ALONE
- MINIMAL_CHANGES
- NO_GOVERNANCE_EDITS
- VALIDATE_IMMEDIATELY

### Coder-SIN-Qwen
| Property | Value |
|----------|-------|
| Model | `vercel/deepseek-v4-flash` |
| Role | Alternative Coder |

### Stealth-Orchestrator
| Property | Value |
|----------|-------|
| Model | `vercel/deepseek-v4-flash` |
| Role | Browser Automation |

---

## Simone-MCP Integration

**Source**: https://github.com/Delqhi/Simone-MCP

Every Code-Swarm agent uses **Simone-MCP** for AST-level code operations via MCP 2.0 protocol.

### Simone-MCP Tools

| Tool | Type | Description |
|:---|:---|:---|
| `code.find_symbol` | Read | Locate symbol definitions across workspace |
| `code.find_references` | Read | Find textual references to a symbol |
| `code.replace_symbol_body` | Write | Replace the body of a Python function |
| `code.insert_after_symbol` | Write | Insert text immediately after a symbol block |
| `code.project_overview` | Read | Summarize workspace footprint and file types |

### Deployment

**Local Development:**
```python
from simone_mcp.client import SimoneClient
from simone_mcp.bridge import SwarmSimoneBridge

bridge = SwarmSimoneBridge(local=True)
await bridge.analyze_code("MyClass")
```

**Production (OCI VM):**
```
ubuntu@92.5.60.87:8234
```

---

## SOTA Implementation

### P0 - Production Critical
- [x] **Data Persistence**: PostgreSQL schema + Redis cache + S3 storage + pgvector
- [x] **Monitoring**: Prometheus metrics + OpenTelemetry tracing + Health checks
- [x] **Security**: OAuth2/JWT auth + RBAC permissions + bcrypt
- [x] **Testing**: Unit tests + Integration tests + Load tests (Locust)

### P1 - High Value
- [x] **API Gateway**: FastAPI REST + OpenAPI/Swagger + Rate limiting
- [x] **Kubernetes**: Helm chart + HPA auto-scaling + Istio
- [x] **WebSockets**: Real-time agent status + Live task updates
- [x] **CLI**: Rich output + Progress bars + Typer
- [x] **Documentation**: MkDocs + Swagger

### P2 - Optimization
- [x] **Self-Improvement**: RLHF feedback loops + Bayesian optimization

---

## Quick Start

```bash
# Clone and install
gh repo clone OpenSIN-Code/Code-Swarm
cd Code-Swarm
pip install -r requirements.txt

# Copy configs to opencode
cp configs/opencode.json ~/.config/opencode/opencode.json
cp configs/oh-my-opencode.json ~/.config/opencode/oh-my-opencode.json

# Run tests
pytest tests/unit/

# Start API server
uvicorn api.main:app --reload

# CLI commands
python -m cli.main status
```

---

## Architecture

```
SIN-Zeus (Fleet Commander)
├── hermes (Dispatcher) → Fireworks AI + Simone-MCP
├── prometheus (System Planner) → Fireworks AI + Simone-MCP
├── zeus (Validation Superlayer) → Fireworks AI
├── atlas (Backend Engineer) → Fireworks AI + Simone-MCP
├── SIN-Solo (Direct Executor) → Vercel DeepSeek V4 Pro
├── multimedia_looker (Vision) → NVIDIA Nemotron 3 Nano Omni
└── LangGraph Pipeline (StateGraph + Simone-MCP + Feedback Loops)
```

---

## GitHub Issues

| # | Status | Description |
|---|--------|-------------|
| #15 | ✅ Epic | Simone-MCP Full Integration |
| #16 | 🔧 TODO | Deploy Simone-MCP on OCI VM |
| #17 | 🔗 TODO | Configure endpoint |
| #18 | 🧠 TODO | LangGraph integration |
| #19 | 💾 TODO | Hybrid memory |
| #20 | ⚙️ TODO | opencode.json MCP config |
| #21 | ✅ Epic | SIN-Zeus & SIN-Solo Fusion |

---

## Model Hierarchy

| Modell | Agenten | Provider |
|--------|---------|----------|
| `fireworks-ai/minimax-m2.7` | SIN-Zeus, coder-sin-swarm, hermes, prometheus, zeus, atlas, hephaestus | Fireworks AI |
| `vercel/deepseek-v4-flash` | Coder-SIN-Qwen, Stealth-Orchestrator, 10 Subagenten | Vercel |
| `vercel/deepseek-v4-pro` | SIN-Solo | Vercel |
| `nvidia/nvidia/nemotron-3-nano-omni` | multimedia_looker | NVIDIA |
| `groq/whisper-large-v3` | audio_agent | Groq |
| **Simone-MCP (MCP 2.0)** | **Alle 22 Agenten** | **AST-Level Operations** |

---

## Tools

OpenCode provides various tools for different tasks:

- [`look_at`](./docs/tools/look_at.md) - Extract basic information from media files (PDFs, images, diagrams)

For full tool documentation, see the [Tools Reference](./docs/tools/README.md).

---

## Documentation

The monolithic `AGENTS.md` has been migrated to a modular documentation structure:

### Quick Links

| Category | Path | Description |
|----------|------|-------------|
| **Rules** | [`docs/rules/`](./docs/rules/README.md) | All operational rules |
| **Core** | [`docs/rules/core/`](./docs/rules/core/README.md) | Vision Gate, Anti-Loops |
| **Design** | [`docs/rules/design/`](./docs/rules/design/design-routing.md) | Design task routing |
| **LLM** | [`docs/rules/llm/`](./docs/rules/llm/llm-calls.md) | LLM call rules |
| **Browser** | [`docs/rules/browser/`](./docs/rules/browser/chrome-session.md) | Chrome & automation |
| **Configuration** | [`docs/configuration/`](./docs/configuration/README.md) | Models & plugins |
| **Migration** | [`docs/MIGRATION.md`](./docs/MIGRATION.md) | AGENTS.md → modular docs |

### MkDocs

This repo has full MkDocs support. Run:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

For full documentation site, see [mkdocs.yml](./mkdocs.yml).

---