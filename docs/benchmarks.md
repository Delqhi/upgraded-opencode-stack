# Benchmarks

**Status: Pending public run, target v0.2.0.**

We will not publish unverified benchmark numbers. This page documents our methodology and will be updated with verified results when the v0.2.0 milestone runs them publicly.

## Why benchmarks matter

Coding agents are an unusually noisy product space. README claims like "SOTA" or "beats Antigravity" mean nothing without a reproducible benchmark on a public test set. Our policy:

> No benchmark number is published until it has been run with our public harness, on a published commit SHA, against a public dataset, with logs.

## Planned benchmarks

| Benchmark | Dataset size | Why |
|---|---|---|
| **swe-bench Lite** | 300 tasks | Industry standard; Aider, Cline, OpenHands, Cursor all report this |
| **HumanEval-X** | 164 × 5 langs | Multi-language correctness |
| **swe-bench Verified** | 500 tasks | Stricter superset; differentiates top tier |
| **MultiPL-E** | ~6k | Cross-language generalization |

## Reference numbers (from public sources, not our runs)

For context only. These are competitor-reported numbers, dated 2025–2026. We will publish ours next to theirs once we run.

| System | swe-bench Lite | swe-bench Verified | Source |
|---|:-:|:-:|---|
| Aider (Claude 3.5 Sonnet) | ~26% | ~18% | aider.chat/blog |
| OpenHands (CodeAct + GPT-4o) | ~33% | ~22% | github.com/OpenHands |
| Cursor Agent | ~30% | ~25% | cursor.com/blog |
| Anthropic Claude Code | ~49% | ~39% | anthropic.com |
| **OpenSIN (planned target)** | **>35%** | **>25%** | This site, when measured |

We are not setting unrealistic targets. We are setting honest "beat the median open-source agent" targets and will iterate.

## Methodology

When we run, the harness will be:

1. **Code:** [`Code-Swarm/benchmarks/swe_bench/`](https://github.com/OpenSIN-Code/Code-Swarm) (in active development)
2. **Models:** documented per run; we do not benchmark on private models
3. **Reproducibility:** every run is a tagged commit, JSONL output, and a published log
4. **Harness:** the upstream `swe-bench` harness, no custom prompt engineering tricks
5. **Disclosure:** any failures, retries, or environment differences are listed

## Subscribe to the v0.2.0 result

- Watch [Code-Swarm releases](https://github.com/OpenSIN-Code/Code-Swarm/releases)
- Follow the [v0.2.0 milestone](https://github.com/OpenSIN-Code/Code-Swarm/milestones)
- [Sponsor the project](sponsor.md) — paid LLM credits go directly into benchmark runs

If you want to help us run the harness, the issue is open: [Code-Swarm#bench](https://github.com/OpenSIN-Code/Code-Swarm/issues).
