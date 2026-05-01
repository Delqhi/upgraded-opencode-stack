---
name: doctor
description: Universal repo health auditor. Multi-lens deep scan: documentation truthfulness, code quality, cross-repo consistency, config drift, security gaps, and methodological correctness. Produces P0/P1/P2 findings with file:line evidence. Works on ANY repo or multi-repo workspace.
license: MIT
compatibility: opencode
metadata:
  audience: all-agents
  workflow: universal-repo-health-audit
  trigger: doctor, audit, gesund, reinigen, health-check, diagnose, prüfe, check docs, sauber machen
---

# /doctor — Universal Repo Health Auditor (SOTA v3)

> Universell. Für JEDES Repo. 7 Lenses. P0/P1/P2. Quick + Deep.

```
/doctor           → Quick-Scan (Key-Files, ~15s)
/doctor deep      → Deep-Scan (ALL files, ~60s)
/doctor --fix     → Auto-Fix sicherer Probleme
/doctor --checklist → Zeigt SOTA-Doc-Checkliste
```

---

## Phase 0: Discovery

- `.opencode/workspace.yaml` → Multi-Repo oder Single-Repo
- Repo-Typ: Python/JS/TS/Rust/Go/Swift, App/CLI/Lib/Config, aktiv/archiviert

---

## Phase 1: Diagnose — 7 Lenses + SOTA Checklist

### 🔍 Lens 1: Documentation Truthfulness

Behaupten Docs Dinge, die der Code nicht hält? README-Claims vs CLI-Flags, brain.md-Mechanismen vs Source.

### 🔍 Lens 2: Methodological Correctness

Existieren genannte APIs/Funktionen/Flags? Tote Technologien?

### 🔍 Lens 3: Cross-Repo Consistency

Gleiche LICENSE? workspace.yaml in jedem Repo? AGENTS.md-Cross-Refs?

### 🔍 Lens 4: Documentation Completeness (SOTA Checklist)

Prüft gegen die definitive 57-Dateien-Checkliste:

**GitHub Community Standards (7):** README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT, CODEOWNERS

**OpenSSF/Apache Maturity (9):** GOVERNANCE, MAINTAINERS, AUTHORS, CHANGELOG, CITATION.cff, DEPENDENCIES, RELEASE, STYLEGUIDE, CODE_REVIEW_GUIDELINES

**SIN-CLIs Spezifisch (18):** goal, architecture, brain, issues, fix, successful, roadmap, PROPOSAL, AGENTS, design, api, usage, faq, troubleshooting, testing, benchmarks, acknowledgments, ADR

**Tooling (5):** Makefile, .gitignore, .env.example, DCO, NOTICE

**GitHub Templates (6):** ISSUE_TEMPLATE/bug, ISSUE_TEMPLATE/feature, PULL_REQUEST_TEMPLATE, FUNDING, dependabot, config.yml

**Optionals (12):** .editorconfig, .markdownlint.json, .gitattributes, docs/, examples/, docker-compose.yml, Dockerfile, TRANSLATION, THIRD_PARTY_LICENSES, CONTRIBUTORS, HISTORY, .all-contributorsrc

### 🔍 Lens 5: Code Quality Surface

package.json/pyproject.toml? Tests + Linter + CI? .gitignore? Type-Hints?

### 🔍 Lens 6: Secrets & Config Hygiene

.env mit Keys? .env.example fehlt? Hartcodierte API-Keys?

### 🔍 Lens 7: Repository Metadata

Description + Topics? Default Branch? Issues/PRs aktiv?

---

## Phase 2: Diagnose-Report

```markdown
# 🩺 Doctor Audit — REPO_NAME

**Score: 85/100 (B+)** | Mode: deep | Lenses: 7/7 | SOTA Docs: 42/57

## 🔴 P0 — Critical

| # | Lens | File:Line | Finding |

## 🟡 P1 — High

| # | Lens | File:Line | Finding |

## 🟢 P2 — Medium

| # | Lens | File:Line | Finding |
```

---

## Phase 3: Behandlung (`--fix`)

**Auto:** Veraltete Claims ersetzen, workspace.yaml, Cross-Refs, ⚠️-Header, .editorconfig, .gitattributes, fehlende Templates

**Semi:** brain.md updaten, README korrigieren, Versionen syncen

**Manuell:** Lizenz-Konflikte, Architektur-Änderungen

---

## Phase 4: Nachsorge

- Final Audit: Score muss steigen
- Commit: `docs: doctor-audit — GEFIXTES`
- Health-Trend: `.opencode/doctor-history.json`
