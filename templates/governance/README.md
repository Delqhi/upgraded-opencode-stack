# Governance Contract Templates

> **Canonical templates for sovereign repo governance across the OpenSIN fleet.**
> Version: 2026.04.17 | Issue: upgraded-opencode-stack#26

## Overview

This directory contains **concrete template instances** that any A2A repo can copy to bootstrap its governance stack. The corresponding JSON Schemas live in the parent `templates/` directory.

## Files

| File                              | Purpose                                               | Copy To                           |
| --------------------------------- | ----------------------------------------------------- | --------------------------------- |
| `repo-governance.template.json`   | Branch protection, merge rules, fail-closed semantics | `governance/repo-governance.json` |
| `pr-watcher.template.json`        | PR review automation, credential scanning, escalation | `governance/pr-watcher.json`      |
| `platform-registry.template.json` | Platform intake registry with fail-closed rules       | `platforms/registry.json`         |

## Usage

### For New Repos (via Factory)

The factory (`create-sin-a2a-agent.mjs`) reads `Template-SIN-Agent/required-files.manifest.json` and copies these templates automatically during repo generation, substituting `{{REPO_SLUG}}` with the actual agent slug.

### For Existing Repos (via Backfill)

```bash
# Copy and customize for your repo
cp templates/governance/repo-governance.template.json governance/repo-governance.json
cp templates/governance/pr-watcher.template.json governance/pr-watcher.json
cp templates/governance/platform-registry.template.json platforms/registry.json

# Replace placeholder with actual repo slug
sed -i '' 's/{{REPO_SLUG}}/your-agent-slug/g' governance/*.json platforms/*.json
```

### Validation

Validate your governance files against the schemas:

```bash
# Using ajv-cli or similar JSON Schema validator
ajv validate -s templates/repo-governance.schema.json -d governance/repo-governance.json
ajv validate -s templates/pr-watcher.schema.json -d governance/pr-watcher.json
ajv validate -s templates/platform-registry.schema.json -d platforms/registry.json
```

## Schema Reference

| Schema                          | Location                                  |
| ------------------------------- | ----------------------------------------- |
| `repo-governance.schema.json`   | `templates/repo-governance.schema.json`   |
| `pr-watcher.schema.json`        | `templates/pr-watcher.schema.json`        |
| `platform-registry.schema.json` | `templates/platform-registry.schema.json` |
| `work-item.schema.json`         | `templates/work-item.schema.json`         |

## Template Variables

All templates use `{{REPO_SLUG}}` as the primary substitution variable. The factory replaces this with the agent's actual slug during generation.

## Relationship to Template-SIN-Agent

These templates are the **source of truth** for governance file content. `Template-SIN-Agent` contains its own copies (in `governance/`, `platforms/`) but those are generated FROM these templates. When updating governance contracts, update HERE first, then propagate to Template-SIN-Agent.

## Fail-Closed Rules

All governance contracts follow fail-closed semantics:

- Unknown check results → **block** (not pass)
- Missing required files → **block merge**
- Credential leaks → **block merge immediately**
- Unregistered platforms → **blocked** (no implicit access)
- CI runner timeout → **block** (not skip)
