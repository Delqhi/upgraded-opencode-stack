# Performance Optimization Guide

## Model Selection Strategy

| Task Type | Model | Avg Response |
|:---|:---|:---|
| Quick lookup | `nvidia-nim/stepfun-ai/step-3.5-flash` | ~0.5s |
| Code generation | `google/antigravity-claude-sonnet-4-6` | ~2-5s |
| Architecture | `google/antigravity-claude-opus-4-6-thinking` | ~10-30s |
| Research | `google/antigravity-gemini-3.1-pro` | ~3-8s |

## Parallel Exploration

Always use 5-10 parallel explore/librarian agents for large codebases.

## Token Optimization

- Keep prompts under 50% of context window
- Use `task()` for delegation
- Use `load_skills=[]` to avoid unnecessary injection
- Use `--format json` for structured output

## Fallback Chain (fastest first)

1. `nvidia-nim/stepfun-ai/step-3.5-flash` — ~0.5s
2. `google/antigravity-gemini-3-flash` — ~1s
3. `openai/gpt-5.4` — ~2s
4. `google/antigravity-gemini-3.1-pro` — ~3s
5. `qwen/coder-model` — ~2s

## Monitoring Metrics

- Average response time: <3s target
- Token usage: <50K tokens per request
- Fallback rate: <5%
- Error rate: <1%
