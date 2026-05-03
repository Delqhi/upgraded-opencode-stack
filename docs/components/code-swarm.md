# Code-Swarm

**The 22-agent fleet backend.** Repo: [OpenSIN-Code/Code-Swarm](https://github.com/OpenSIN-Code/Code-Swarm). Latest release: [`v0.1.0-alpha`](https://github.com/OpenSIN-Code/Code-Swarm/releases/tag/v0.1.0-alpha).

## What it does

Code-Swarm is the multi-agent orchestration layer. The OpenSIN-Code CLI delegates large or parallel tasks to it. It exposes a dual-protocol API (FastAPI REST + gRPC) with WebSocket streaming for real-time agent status.

## Components

| Layer | Tech |
|---|---|
| API | FastAPI + gRPC dual-protocol gateway, rate limiting |
| Orchestration | LangGraph state machine |
| Agents | 22-agent registry (planner, coder, reviewer, debugger, ...) |
| Streaming | WebSocket real-time status feed |
| Auth | JWT + RBAC, env-driven `SECRET_KEY` |
| Storage | Postgres + Redis + S3-compatible blob (configurable) |
| Observability | Prometheus metrics + structured logging + health endpoints |
| Tools | MCP 2.0 client → Simone-MCP for AST-level edits |

## Install

```bash
git clone https://github.com/OpenSIN-Code/Code-Swarm
cd Code-Swarm
cp .env.example .env
# Edit .env: SECRET_KEY (required in production), ALLOWED_ORIGINS, etc.
pip install -r requirements.txt
python -m cli.main status
```

## Required environment

| Variable | Required in production | Purpose |
|---|---|---|
| `SECRET_KEY` | yes | JWT signing |
| `ALLOWED_ORIGINS` | yes | CORS whitelist |
| `ENVIRONMENT` | optional | `development` (default) or `production` |
| `CODE_SWARM_BASE_DIR` | optional | Data directory override |

## Status

- Core API + auth + WebSocket streaming: **shipped in v0.1.0-alpha**
- 22-agent registry skeleton: **shipped**
- LangGraph + Simone-MCP integration: **shipped**
- swe-bench harness: **in development for v0.2.0**
- PyPI distribution: **in development for v0.2.0**

## Known gaps for v0.2.0

- Published swe-bench Lite + Verified scores
- `pip install code-swarm` from PyPI (currently git-only)
- Real RLHF feedback loop (currently stub)
- Full integration test coverage (currently unit + scaffolding)
