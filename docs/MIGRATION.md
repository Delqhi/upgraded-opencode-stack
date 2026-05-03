# Migration Guide: From AGENTS.md to Modular Docs

## Overview

The monolithic AGENTS.md (1439 lines) has been split into a modular documentation structure.

## New Structure

```
docs/
├── rules/
│   ├── core/
│   │   ├── vision-gate.md
│   │   ├── anti-loops.md
│   │   └── README.md
│   ├── design/
│   │   └── design-routing.md
│   ├── llm/
│   │   └── llm-calls.md
│   └── browser/
│       ├── chrome-session.md
│       ├── browser-automation.md
│       └── README.md
├── configuration/
│   └── models.md
└── tools/
    └── look_at.md
```

## Migration Status

✅ **Phase 1**: Split AGENTS.md into modular structure
✅ **Phase 2**: Update all references
✅ **Phase 3**: Create migration documentation

## How to Use

Replace references to AGENTS.md with the appropriate modular file:

| Old Section | New File |
|-------------|----------|
| Vision Gate | `docs/rules/core/vision-gate.md` |
| Design Routing | `docs/rules/design/design-routing.md` |
| LLM Calls | `docs/rules/llm/llm-calls.md` |
| Chrome Rules | `docs/rules/browser/chrome-session.md` |
| Browser Automation | `docs/rules/browser/browser-automation.md` |
