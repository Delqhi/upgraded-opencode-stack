# Honest comparison vs Aider, Cline, OpenHands, Cursor, Antigravity

We hold ourselves to honest comparisons. This page lists what each system does well and where OpenSIN currently is — including where we still lose.

## Capability matrix

| Capability | OpenSIN | Aider | Cline | OpenHands | Cursor | Antigravity |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| MIT / Apache OSS | yes | yes | yes | yes | no | no |
| Free for end-users | yes | yes | yes | yes | no | partial |
| Bring-your-own LLM keys | yes | yes | yes | yes | no | no |
| CLI | yes | yes | no | yes | no | no |
| IDE / VS Code extension | yes | no | yes | no | yes | yes |
| Multi-agent fleet | yes | no | no | yes | no | no |
| AST-level symbol edits | yes | no | no | no | no | no |
| Browser automation | yes | no | no | partial | no | yes |
| macOS computer-use | yes | no | no | no | no | yes |
| Self-hostable | yes | yes | yes | yes | no | no |
| Free infra defaults (OCI A1.Flex) | yes | no | no | no | no | no |
| MCP 2.0 native | yes | no | yes | partial | partial | no |
| A2A protocol native | yes | no | no | no | no | no |
| Published swe-bench score | **pending** | yes | yes | yes | yes | yes |
| GitHub stars | early | 30k+ | 25k+ | 50k+ | n/a | n/a |
| Production-ready today | **no** | yes | yes | yes | yes | yes |

## Where OpenSIN currently loses

**1. Adoption.** Aider, Cline, and OpenHands have years of iteration and tens of thousands of users. We have weeks. Until our v0.2.0 ships with a published benchmark and PyPI/npm distribution, the smart money is still on the incumbents.

**2. Polish.** Aider's `aider` command "just works" in any git repo. Cline has a beautiful VS Code panel. We require a multi-step setup today. v0.2.0 fixes this.

**3. Benchmarks.** Aider, Cline, OpenHands, Cursor, and Antigravity all publish swe-bench Lite scores. We have not run the benchmark publicly yet. **This is our biggest credibility gap and our top v0.2.0 priority.**

**4. Documentation depth.** Aider's docs are 80+ pages of recipes. Ours are this site, today. Closing the gap is in scope for v0.2.0.

## Where OpenSIN already wins

**1. AST-level symbol edits via MCP.** No competitor offers `find_symbol` / `replace_symbol_body` / `insert_after_symbol` as standardized MCP tools. Aider does text diffs. Cline does context windows. We do symbol surgery. This means smaller patches, fewer hallucinated edits, and surgical refactors that other tools cannot match.

**2. Multi-agent fleet + CLI + IDE in one stack.** Aider is CLI-only. Cline is IDE-only. OpenHands is CLI + sandbox but no IDE plugin. We ship all three (CLI, VS Code extension, fleet backend) under one MIT roof.

**3. Browser + macOS computer-use, free.** Antigravity has both, but it's paid and tied to Google. We have both, MIT, and self-hostable.

**4. Free-stack infrastructure strategy.** Every default deploy target uses Oracle Cloud A1.Flex (always-free 24 GB RAM ARM) + Cloudflare Workers. No competitor optimizes for zero-cost self-hosting at the infra layer.

**5. MCP 2.0 + A2A protocol native.** We are not a proprietary platform. Every component speaks open protocols and can be swapped. Cursor and Antigravity cannot claim this.

## Decision guide — which should you use?

- **You want it now, in production:** use Aider, Cline, or OpenHands. They have shipped.
- **You want a managed paid product:** use Cursor or Antigravity.
- **You want the most capable open-source stack and you are willing to be early:** use OpenSIN. Star the repos. File issues. Help us close the v0.2.0 gap.

## How we will close the gap

Tracked in our [public roadmap](index.md#roadmap-to-v020):

1. swe-bench Lite + HumanEval-X scored against Aider / OpenHands by v0.2.0
2. PyPI + npm + brew distribution
3. Full docs site with 50+ pages of recipes
4. TLS-fronted MCP bridge for production deployments
5. Real RLHF feedback loop (currently stub)

If you can help with any of these, [open a PR](https://github.com/OpenSIN-Code) or [sponsor the project](sponsor.md).
