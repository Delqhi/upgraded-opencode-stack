# Quickstart

Get the full OpenSIN stack running in under 5 minutes. All components are MIT-licensed and run free with your own LLM API keys.

## Prerequisites

- **Python 3.11+** for Code-Swarm and Simone-MCP
- **Bun 1.x** for the OpenSIN-Code CLI (see [bun.sh](https://bun.sh))
- **Git**
- One LLM API key (Anthropic, OpenAI, or any AI Gateway provider)

## 1. The CLI — `opensin-code`

The CLI is the user-facing entry point. It spans browser automation, macOS computer-use, and orchestrates the rest of the stack.

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
# or
export OPENAI_API_KEY=sk-...
```

## 2. The Backend — Code-Swarm

Code-Swarm is the multi-agent fleet that the CLI delegates large tasks to. Run it locally or on an OCI A1.Flex VM.

```bash
git clone https://github.com/OpenSIN-Code/Code-Swarm
cd Code-Swarm
cp .env.example .env
# Edit .env: set SECRET_KEY and ALLOWED_ORIGINS
pip install -r requirements.txt
python -m cli.main status
```

Required environment variables (see [.env.example](https://github.com/OpenSIN-Code/Code-Swarm/blob/main/.env.example)):

| Variable | Required in production | Purpose |
|---|---|---|
| `SECRET_KEY` | yes | JWT signing |
| `ALLOWED_ORIGINS` | yes | CORS whitelist (comma-separated) |
| `ENVIRONMENT` | optional | `development` (default) or `production` |
| `CODE_SWARM_BASE_DIR` | optional | Override data directory |

## 3. The AST Engine — Simone-MCP

Simone-MCP is the surgical symbol-level edit layer. It can run as a local stdio MCP server or as a remote HTTP service.

```bash
git clone https://github.com/Delqhi/Simone-MCP
cd Simone-MCP
pip install -e .
simone-mcp serve --transport stdio
```

Then point your MCP client at it:

```json
{
  "mcpServers": {
    "simone": {
      "command": "simone-mcp",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

## 4. Kubernetes — production deploy

For multi-node deploys, use the [kubernetes-sota-practices](https://github.com/OpenSIN-Code/kubernetes-sota-practices) repo:

```bash
git clone https://github.com/OpenSIN-Code/kubernetes-sota-practices
cd kubernetes-sota-practices
helm install code-swarm ./helm/code-swarm --namespace opensin --create-namespace
```

Includes Istio service mesh, HPA, PDB, Prometheus + Grafana dashboards.

## Verify everything works

```bash
# Backend health
curl http://localhost:8000/health

# CLI status
opensin status

# MCP server check
simone-mcp ping
```

## Next steps

- [Architecture deep-dive](architecture.md)
- [How OpenSIN compares to Aider, Cline, OpenHands, Cursor, Antigravity](compare.md)
- [Component deep-dives](components/code-swarm.md)
- [Sponsor the project](sponsor.md)
