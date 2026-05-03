# OpenSIN — Free, MIT-licensed Coding Agents

**The most comprehensive open-source coding agent stack — built to beat paid systems while staying free for end users.**

OpenSIN is a portfolio of four MIT-licensed projects that together form a complete coding agent platform: a 22-agent fleet backend, a CLI with browser & macOS computer-use, an AST-precise MCP server, and SOTA Kubernetes deployment patterns. Every component runs on free infrastructure (Oracle Cloud A1.Flex) with bring-your-own API keys.

[Get started in 60 seconds](quickstart.md){ .md-button .md-button--primary }
[Compare vs Aider / Cline / OpenHands](compare.md){ .md-button }
[Sponsor on GitHub](sponsor.md){ .md-button }

---

## Components

| Component | What it does | Status | Repo |
|---|---|---|---|
| **[Code-Swarm](components/code-swarm.md)** | 22-agent fleet backend (FastAPI + gRPC + WebSockets) | `v0.1.0-alpha` | [OpenSIN-Code/Code-Swarm](https://github.com/OpenSIN-Code/Code-Swarm) |
| **[OpenSIN-Code CLI](components/opensin-code.md)** | Coding agent CLI with browser & macOS computer-use | `v0.1.0-alpha` | [OpenSIN-Code/OpenSIN-Code](https://github.com/OpenSIN-Code/OpenSIN-Code) |
| **[Simone-MCP](components/simone-mcp.md)** | AST-level symbol operations as an MCP server | `v0.1.0-alpha` | [Delqhi/Simone-MCP](https://github.com/Delqhi/Simone-MCP) |
| **[Kubernetes-SOTA](components/kubernetes.md)** | Helm charts, Istio, k3s, monitoring for the fleet | `v0.1.0-alpha` | [OpenSIN-Code/kubernetes-sota-practices](https://github.com/OpenSIN-Code/kubernetes-sota-practices) |

---

## Why OpenSIN

### What others have

| Capability | Aider | Cline | OpenHands | Cursor | Antigravity |
|---|:-:|:-:|:-:|:-:|:-:|
| Free / OSS | yes | yes | yes | no | no |
| Multi-agent fleet | no | no | yes | no | no |
| Browser automation | no | no | partial | no | yes |
| macOS computer-use | no | no | no | no | yes |
| AST-level symbol edits | no | no | no | no | no |
| Self-hosted on free infra | yes | yes | yes | no | no |

### What OpenSIN has

- **All of the above, in one MIT stack.** Multi-agent fleet (Code-Swarm) + CLI with browser/macOS use (OpenSIN-Code) + AST symbol surgery (Simone-MCP).
- **Bring-your-own keys.** You pay your LLM provider directly. We never proxy, never bill, never lock in.
- **Zero-billing infrastructure.** Every default deploy target is Oracle Cloud A1.Flex (free tier, 24 GB RAM ARM64) plus Cloudflare Workers for edge. No SaaS dependency.
- **MCP 2.0 + A2A protocol native.** Open standards only. Every component is replaceable.

See the full honest comparison in [compare](compare.md).

---

## Quickstart

```bash
# 1. CLI (TypeScript)
git clone https://github.com/OpenSIN-Code/OpenSIN-Code
cd OpenSIN-Code && bun install && bun run build

# 2. Backend (Python)
git clone https://github.com/OpenSIN-Code/Code-Swarm
cd Code-Swarm && cp .env.example .env  # set SECRET_KEY + ALLOWED_ORIGINS
pip install -r requirements.txt && python -m cli.main status

# 3. AST tooling (Python)
git clone https://github.com/Delqhi/Simone-MCP
cd Simone-MCP && pip install -e . && simone-mcp --help
```

Full guide: [quickstart](quickstart.md).

---

## Architecture at a glance

```
                       ┌─────────────────────────────────┐
   You (BYO keys) ───▶ │   OpenSIN-Code CLI (TypeScript) │ ◀─── Browser + macOS
                       │   SIN-Zeus  │  SIN-Solo         │      Computer-Use
                       └──────────┬──────────────────────┘
                                  │ MCP 2.0 / A2A
                       ┌──────────▼──────────┐    ┌──────────────────┐
                       │  Code-Swarm (Py)    │ ──▶│  Simone-MCP      │
                       │  22-agent fleet     │    │  AST symbol ops  │
                       │  FastAPI + gRPC     │    └──────────────────┘
                       └──────────┬──────────┘
                                  │
                       ┌──────────▼──────────────────┐
                       │  Kubernetes-SOTA practices  │
                       │  Helm + Istio + k3s on OCI  │
                       └─────────────────────────────┘
```

Full diagram + deep-dive: [architecture](architecture.md).

---

## Roadmap to v0.2.0

- [ ] Published swe-bench Lite + HumanEval-X scores vs Aider / OpenHands
- [ ] PyPI: `pip install code-swarm` and `pip install simone-mcp`
- [ ] npm: `npm i -g opensin-code`
- [ ] Brew tap: `brew install opensin-code`
- [ ] TLS + cert-manager for the public OCI MCP bridge
- [ ] Real RLHF feedback loop (currently stub)

[Track progress on GitHub](https://github.com/OpenSIN-Code) · [Sponsor](sponsor.md) · [Discussions](https://github.com/OpenSIN-Code/Code-Swarm/discussions)

---

License: **MIT**. Built by [@Delqhi](https://github.com/Delqhi) and the OpenSIN community.
