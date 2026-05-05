---
name: create-flow
description: Build interactive flows with atomic single-action steps, screenshot + vision gating, local brain evidence, and tiered autorun promotion (run → mini → low → high → max → full) only after 10 consecutive successful validations per tier.
compatibility: opencode
metadata:
  audience: all-agents
  workflow: flow-building
---

# Create Flow

Fast, safe flow construction for browser, GUI, and terminal work.

## Rules

- One action per run.
- Every action gets a screenshot.
- Every screenshot gets a vision verdict.
- Every verdict is written to the local brain.
- Promotion only happens from evidence.
- If no `--root` is given, the flow root is auto-detected from the current git repo.
- Screenshot + vision analysis are captured in one step and stored next to the flow evidence.
- Vision analysis must use the Antigravity plugin model `google/antigravity-gemini-3-flash` directly.
- Never use the direct Gemini API.
- The skill fails fast if the required flash vision path is unavailable.

## Tier ladder

| Tier   | Meaning                   | Promotion rule                        |
| ------ | ------------------------- | ------------------------------------- |
| `run`  | atomic action             | 2 successes → 1 `mini` candidate      |
| `mini` | two proven runs           | 10 clean candidates → approved `mini` |
| `low`  | two approved `mini` units | 10 clean candidates → approved `low`  |
| `high` | two approved `low` units  | 10 clean candidates → approved `high` |
| `max`  | two approved `high` units | 10 clean candidates → approved `max`  |
| `full` | two approved `max` units  | 10 clean candidates → full autorun    |

## Local brain layout

```text
<repo>/.opencode/flows/<flow-slug>/
├── brain.md
├── flow.md
├── state.json
├── agent_workflow_master.json   ← Dual-Logger merged output
├── evidence/
│   └── <step-id>/
│       ├── screenshot.png
│       ├── vision.txt
│       ├── analysis.json
│       └── analysis.md
└── archives/
```

## Canonical tools

### CLI

- `sin-flow init <flow>` — scaffold a flow workspace
- `sin-flow step` — execute one action + screenshot + vision + brain log
- `sin-flow keyshot` — screenshot + vision only, writes the same analysis artifacts
- `sin-flow record` — interactive one-action-at-a-time builder
- `sin-flow record-dual` — Dual-Logger recording (OS + browser event capture)
- `sin-flow replay` — replay a recorded workflow with anti-bot countermeasures
- `sin-flow batch` — run a file of single-action steps
- `sin-flow status` — inspect promotion state
- `sin-flow brain` — rebuild the brain from evidence
- `sin-flow archive` — bundle evidence for review/handoff
- `sin-flow guard --repo <path>` — fail when a repo contains divergent `create-flow` runtime files outside the canonical SIN-InkogniFlow / Infra-SIN-OpenCode-Stack layouts

### Anti-Bot & High-Speed Features

- `--mode nodriver` executes Python using an internal `async` context with `nodriver` boilerplate. It injects the `flow_cdp_utils` library automatically.
- `--fast` skips the Vision "Stop & Verify" pause to enable fluid execution (e.g. `Mousedown -> Mouseup -> Click`) for strict bot protections.
- **CDP Helper**: Import `flow_cdp_utils` inside your `nodriver` script for robust float-scaling on Retina, exact mouse event dispatching, and Context-ID logic for incognito windows.
- **Canonical Guard**: `guard_create_flow.py` detects and blocks divergent `create-flow` runtime files in non-canonical repos.

### Dual-Logger Architecture (Human-to-Agent Recording)

The Dual-Logger captures real human workflows and replays them as agent actions with anti-bot countermeasures.

**Components:**

| Component      | File                            | Purpose                                                        |
| -------------- | ------------------------------- | -------------------------------------------------------------- |
| OS Logger      | `dual_logger/os_logger.py`      | pynput + NSWorkspace: mouse, keyboard, window focus            |
| Browser Logger | `dual_logger/browser_logger.js` | Tampermonkey/JS: DOM clicks, inputs, selectors, scrolls        |
| Merge Server   | `dual_logger/agent_logger.py`   | Flask on :5000: merges OS+browser events chronologically       |
| Executor       | `dual_logger/executor.py`       | Replays with Bézier curves, jitter, CDP/pyautogui/hybrid modes |

**Recording:**

```bash
# 1. Start the Dual-Logger recording session
sin-flow record-dual "My Workflow" --root .

# 2. Install browser_logger.js as a Tampermonkey userscript (or inject via nodriver/CDP)

# 3. Perform your human workflow

# 4. Press Ctrl+C to stop — produces agent_workflow_master.json
```

**Replaying:**

```bash
# Hybrid mode (CDP for browser, pyautogui for native apps)
sin-flow replay "My Workflow" --mode hybrid --speed 1.0

# CDP-only (browser events)
sin-flow replay "My Workflow" --mode cdp --cdp-port 9335

# pyautogui-only (native app events)
sin-flow replay "My Workflow" --mode pyautogui --speed 2.0
```

**Anti-bot countermeasures in the executor:**

- Bézier curve mouse movement (not linear — mimics human hand tremor)
- Timestamp-based inter-event delays (preserves original human timing)
- Random jitter on coordinates (±2px) and delays (±50ms Gaussian)
- Gaussian-distributed typing speed variation
- Ghost-cursor-style mouse trail with overshoot on long distances

### API

- `sin-flowd` — local HTTP daemon
- `sin-eye` — optional ultra-fast vision backend when installed
- `POST /v1/flows` — create workspace
- `POST /v1/flows/<slug>/step` — run one step
- `POST /v1/flows/<slug>/keyshot` — capture + verify only
- `GET /v1/flows/<slug>/status` — current ladder state
- `POST /v1/flows/<slug>/brain` — rebuild local brain
- `POST /v1/flows/<slug>/archive` — archive evidence

## Vision chain

Required default:

1. `opencode` + `google/antigravity-gemini-3-flash`

No automatic fallback chain is used by default. If the flash path fails, the step fails fast instead of silently switching models.

`FLOW_VISION_CMD` remains available only for explicit operator overrides.

## Flow files

```bash
python3 ~/.config/opencode/skills/create-flow/scripts/create-flow.py "My Flow" --root .
python3 ~/.config/opencode/skills/create-flow/scripts/sin-flow.py step "My Flow" --action 'tell application "System Events" to key code 48' --expected 'Tab lands on the target'
python3 ~/.config/opencode/skills/create-flow/scripts/sin-flow.py record-dual "My Flow" --root .
python3 ~/.config/opencode/skills/create-flow/scripts/sin-flow.py replay "My Flow" --mode hybrid --speed 1.0
python3 ~/.config/opencode/skills/create-flow/scripts/sin-flowd.py --port 8787 --root .
```

## Hard rules

- Never combine steps before evidence proves it.
- Never promote on intuition.
- Never skip the screenshot.
- Never skip the brain write.
- Never override a real STOP from vision.
- You usually do not need `look_at` for `sin-flow` output; the step already captures and analyzes the screenshot.
