# Architecture

OpenSIN is split into four layers, each replaceable, each speaking open protocols. Every default deploy target runs on free Oracle Cloud A1.Flex infrastructure.

## The four layers

```
┌─────────────────────────────────────────────────────────────────┐
│   Layer 1 — User Surface                                        │
│   OpenSIN-Code CLI (TypeScript / Bun)                           │
│   ├─ SIN-Zeus orchestrator (multi-task fleet driver)            │
│   ├─ SIN-Solo single-agent assistant                            │
│   ├─ Browser-Use plugin (Chromium / Playwright)                 │
│   ├─ macOS Computer-Use plugin                                  │
│   └─ VS Code extension (opensin-code-vscode + kairos-vscode)    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ MCP 2.0 / A2A protocol
┌──────────────────────────────▼──────────────────────────────────┐
│   Layer 2 — Agent Fleet                                         │
│   Code-Swarm (Python / FastAPI + gRPC + WebSockets)             │
│   ├─ 22-agent registry (planner, coder, reviewer, ...)          │
│   ├─ LangGraph orchestration                                    │
│   ├─ Streaming WebSocket status feed                            │
│   ├─ Auth: env-driven SECRET_KEY + JWT + RBAC                   │
│   └─ Observability: Prometheus metrics + structured logs        │
└──────────────────────────────┬──────────────────────────────────┘
                               │ MCP 2.0
┌──────────────────────────────▼──────────────────────────────────┐
│   Layer 3 — Code-Aware Tools                                    │
│   Simone-MCP (Python)                                           │
│   ├─ AST-level: find_symbol, replace_symbol_body, ...           │
│   ├─ Tree-sitter multi-language                                 │
│   └─ HTTP and stdio transports                                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ Helm / kubectl
┌──────────────────────────────▼──────────────────────────────────┐
│   Layer 4 — Deployment Substrate                                │
│   kubernetes-sota-practices                                     │
│   ├─ Helm charts for every component                            │
│   ├─ Istio service mesh + mTLS                                  │
│   ├─ HPA + PDB for fleet auto-scaling                           │
│   ├─ k3s lightweight cluster bootstrap                          │
│   └─ Prometheus + Grafana monitoring                            │
└─────────────────────────────────────────────────────────────────┘
```

## Why this split

**One CLI, one fleet, one tool layer, one deploy layer.** Each replaceable, each tested in isolation, each speaking an open protocol so anyone can swap in their own component.

- Don't like our CLI? Use the fleet directly with any MCP client (Claude Desktop, Cline, your own).
- Don't like our fleet? Use Simone-MCP standalone with Aider or OpenHands.
- Don't like our K8s charts? Run any component bare-metal — they all expose plain HTTP / stdio.

This is the opposite of Cursor/Antigravity, where every layer is locked to the rest of the proprietary stack.

## Open protocols

| Protocol | Where used | Why |
|---|---|---|
| **MCP 2.0** | CLI ↔ Fleet, Fleet ↔ Simone, third-party tools | Anthropic's open standard; Claude/Cline/OpenHands all speak it |
| **A2A (Agent-to-Agent)** | Fleet inter-agent communication | Open multi-agent message spec |
| **gRPC + Protocol Buffers** | Fleet's high-throughput control plane | Standard, language-agnostic |
| **WebSocket** | Streaming status to CLI | Standard browser-compatible |
| **OpenAPI 3.1** | Fleet REST API | Auto-generated client SDKs |

No proprietary protocols. No client lock-in.

## Free-stack deployment defaults

All components ship with deploy configs targeting **Oracle Cloud A1.Flex** (always-free 24 GB RAM, 4 ARM cores) plus Cloudflare Workers for the edge layer.

- Code-Swarm fits in 8 GB RAM
- Simone-MCP fits in 4 GB RAM
- k3s control plane fits in 2 GB RAM
- Remaining 10 GB headroom for caching, MCP bridges, n8n workflows

You bring your LLM API key. We never proxy it. The OpenSIN platform itself costs €0 to run.

## Security model

**Code-Swarm** (post-CEO-Audit Sev-1 fixes):

- `SECRET_KEY` from environment, refused if production starts without it
- `ALLOWED_ORIGINS` whitelist, CORS wildcards rejected
- Explicit method/header allow-lists
- bcrypt password hashing, JWT bearer tokens, RBAC enforced

**Simone-MCP** (deploy hardening in progress):

- TLS termination via Caddy / Cloudflare Tunnel (in progress, tracked for v0.2.0)
- mTLS within the K8s mesh via Istio

**OpenSIN-Code CLI**:

- All keys remain on the user's machine
- No telemetry by default
- Optional opt-in usage stats via PostHog (disabled by default)

## Where to learn more

- [Code-Swarm component](components/code-swarm.md)
- [OpenSIN-Code CLI component](components/opensin-code.md)
- [Simone-MCP component](components/simone-mcp.md)
- [Kubernetes-SOTA component](components/kubernetes.md)
- [Honest comparison](compare.md)
