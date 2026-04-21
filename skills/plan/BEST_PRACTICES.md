# OpenSIN Best Practices — Unified Reference

> SSOT for all OpenSIN planning, agent, and infrastructure best practices.
> Updated: 2026-04-13

---

## 1. Planning (`/plan` v2)

### Pipeline Stages
```
0: Check → 1: Research → 1.5: Dependencies → 2: Draft → 2.5: Estimation/Risk
→ 3: Review → 3.2: Quality Score → 3.5: Approval/Sync → 4: Execute
→ 5: Verify → 5.5: Re-Plan → 6: Post-Mortem → 7: Closeout
```

### Mandatory Plan Sections
- **Outcomes/OKRs** — Business/user outcomes, not just tasks
- **Dependency DAG** — Explicit task dependencies with critical path
- **3-Point Estimates** — Pessimistic / Realistic / Optimistic per task
- **Risk Register** — Likelihood × Impact scoring (0-100 overall)
- **Rollback Plan** — Trigger, action, max loss
- **Done Criteria** — Measurable verification conditions

### Quality Gates
- Plan Quality Score ≥ 70/100 (automated calculation)
- All tasks must have 3-point estimates and validation steps
- Risk score ≤ 60 to proceed (re-plan if higher)
- Max 1 revision round after critical review

### Scripts
```bash
# Validate any plan JSON
python3 ~/.config/opencode/skills/plan/scripts/plan_validate.py plan.json --verbose

# Build dependency DAG
python3 ~/.config/opencode/skills/plan/scripts/dag_builder.py plan.json --visualize --output graph.json

# Monte Carlo estimation (10k simulations)
python3 ~/.config/opencode/skills/plan/scripts/monte_carlo.py plan.json --chart --output results.json
```

### Templates
Located at `~/.config/opencode/skills/plan/templates/`:
- `feature-build.json` — New feature development
- `bug-fix.json` — Bug fixes with regression tests
- `migration.json` — System migrations with dual-write
- `refactor.json` — Code refactoring with characterization tests
- `decision-register.md` — Decision tracking template
- `assumptions-log.md` — Assumption tracking with validation

---

## 2. Agent Model Configuration

### Primary Models (opencode.json)
| Agent | Model | Fallback |
|-------|-------|----------|
| explore, librarian, general, oracle | `qwen/coder-model` | `qwen/coder-model` |
| All other agents | `qwen/coder-model` | `qwen/coder-model` |

### Provider Config
| Provider | Models | Base URL |
|----------|--------|----------|
| **qwen** | `coder-model`, `vision-model` | `https://portal.qwen.ai/v1` |
| **openai** | `gpt-5.4` | OCI Proxy `:4100` |
| **google** | `antigravity-*` | Via antigravity plugin |
| **nvidia-nim** | `qwen-3.5-*` | `https://integrate.api.nvidia.com/v1` |

### Qwen Multi-Account Plugin
- **Config**: `~/.config/opencode/qwen-auth-accounts.json`
- **Accounts**: 24 accounts with automated failover
- **Health**: Success/failure tracking, consecutive failure detection
- **Plugin**: `~/.config/opencode/local-plugins/opencode-qwen-auth/`
- **Source**: `Delqhi/upgraded-opencode-stack/local-plugins/opencode-qwen-auth/`

---

## 3. GCP Configuration

### Project: `artificial-biometrics`
- **Account**: `zukunftsorientierte.energie@gmail.com`
- **Service Account**: `ki-agent@artificial-biometrics.iam.gserviceaccount.com`
- **Key**: `~/.config/opencode/auth/google/service-account.json`
- **APIs Enabled**: 41 (including Secret Manager, Gemini, YouTube, Drive, etc.)
- **Secrets**: 4 (groq_api_key_1/2, prolific_email/password)

### Credentials
- **GCP Key**: `~/.config/opencode/auth/google/service-account.json`
- **Qwen Accounts**: `~/.config/opencode/qwen-auth-accounts.json`
- **Antigravity Accounts**: `~/.config/opencode/antigravity-accounts.json`
- **Master Credentials**: `~/.config/opencode/auth/`

---

## 4. A2A-SIN-Google-Apps (Onboarding Orchestrator v2.0)

### Capabilities
- Chrome Password Manager integration (SQLite + Keychain decryption)
- Chrome Cookie/Session extraction
- GCP Secret Manager CRUD
- Browser Automation (AppleScript + CDP)
- 6-Phase Autonomous Onboarding Pipeline

### MCP Tools (35 total)
- `chrome_profiles`, `chrome_passwords_get`, `chrome_passwords_check`
- `chrome_cookies_get`
- `secrets_list`, `secrets_get`, `secrets_create`
- `onboarding_run`, `onboarding_status`
- `browser_check`, `browser_navigate`, `browser_install_extension`
- `system_health`

### Build
```bash
cd /path/to/A2A-SIN-Google-Apps
bun install
bun run build  # Uses build.cjs (TypeScript API)
```

---

## 5. Infrastructure

### OCI VM: `92.5.60.87`
| Service | Port | Purpose |
|---------|------|---------|
| Gateway | 4100 | LLM routing + key rotation |
| Modal Proxy | 8091 | GLM API proxy |
| Pool Service | 8090 | GLM key pool |
| n8n | 5678 | Workflow automation |

### Sync
```bash
sin-sync  # Syncs ~/.config/opencode to OCI VM
```

### Package Manager
- **BUN ONLY** — No npm, no npx (except wrangler/cloudflare CLI)
- `bun install`, `bun run build`, `bun run`

---

## 6. Token Factory (`Delqhi/token-factory`)

### Rotators
| Rotator | Provider | Status |
|---------|----------|--------|
| Antigravity v1.0 | Claude | 🔧 |
| OpenAntigravity Auth | Claude | ✅ |
| OpenAI Temp-Mail | OpenAI | ✅ |
| OpenAI Google | OpenAI | ✅ |
| GLM | Modal | 🔧 |
| **Qwen Multi-Account** | Qwen | ✅ |

---

## 7. Anti-Patterns

| Anti-Pattern | Replacement |
|-------------|-------------|
| Vague quality claims | Concrete gates with pass/fail criteria |
| Story points | PERT 3-point estimation with historical data |
| Static risk matrix | Real-time RAG from CI/CD health, bugs, scope creep |
| Annual batch planning | Continuous planning with decision velocity |
| Planning without outcomes | OKR-first, outcome-driven planning |
| Fictional agent names | Real `task()` with `subagent_type` or `category` |
| Plans without rollback | Every plan needs rollback trigger and action |
| Plans without versioning | Every change increments version with diff |
| npm install | bun install |
| Plans without review | Stage 3 critical review is mandatory |
