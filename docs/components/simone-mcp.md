# Simone-MCP

**AST-level symbol operations as a Model Context Protocol server.** Repo: [Delqhi/Simone-MCP](https://github.com/Delqhi/Simone-MCP). Latest release: [`v0.1.0-alpha`](https://github.com/Delqhi/Simone-MCP/releases/tag/v0.1.0-alpha).

## What it does

Simone-MCP is the surgical-precision edit layer that **no other open-source coding agent has**. While Aider, Cline, and OpenHands operate on text diffs, Simone-MCP operates on **AST symbols**.

This means:

- Smaller patches → less context-window thrashing
- Fewer hallucinated edits → the agent can only target real symbols
- Surgical refactors → rename a function across files in a single tool call
- Multi-language → tree-sitter backend supports Python, TypeScript, Go, Rust, Java, C++, ...

## Tools exposed

| Tool | Purpose |
|---|---|
| `find_symbol` | Locate a class/function/variable definition by name and scope |
| `replace_symbol_body` | Replace the body of a symbol while preserving signature |
| `insert_after_symbol` | Insert new code after a symbol's definition |
| `insert_before_symbol` | Insert new code before a symbol's definition |
| `delete_symbol` | Remove a symbol cleanly, including imports/references when scoped |
| `search_for_pattern` | Multi-file regex with AST-aware filtering |
| `rename_symbol` | Cross-file rename respecting language scoping |

## Install

```bash
git clone https://github.com/Delqhi/Simone-MCP
cd Simone-MCP
pip install -e .
simone-mcp serve --transport stdio
```

Or as remote HTTP service (free OCI A1.Flex deployment):

```bash
simone-mcp serve --transport http --host 0.0.0.0 --port 8080
```

Then point any MCP-aware client at it (Claude Desktop, Cline, OpenSIN-Code CLI, ...).

## Status

- MCP 2.0 server with stdio + HTTP transports: **shipped in v0.1.0-alpha**
- Tree-sitter multi-language backend: **shipped**
- OCI A1.Flex deployment template: **shipped**
- TLS via Caddy / Cloudflare Tunnel: **in progress for v0.2.0**

## Known gaps for v0.2.0

- TLS termination in front of public OCI bridge (currently HTTP-only)
- MCP-Timeout edge case under heavy load (open issue tracked)
- PyPI distribution
- Symbol-graph index for repo-wide refactors

## Why this is our differentiator

Read the [honest comparison](../compare.md) — across 6 coding agent systems, OpenSIN is the only one that exposes AST-level symbol operations as a standardized MCP tool surface. That is our moat.
