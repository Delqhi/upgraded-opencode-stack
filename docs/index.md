# OpenCode Infrastructure Documentation

Welcome to the OpenCode infrastructure documentation. This documentation covers all operational rules, configurations, and tools for the OpenCode agent system.

## 🚀 Quick Start

```bash
# Clone the repository
gh repo clone OpenSIN-Code/infra-opencode-stack
cd infra-opencode-stack

# Install MkDocs
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve
```

## 📚 Documentation Structure

```
docs/
├── rules/             # All operational rules
│   ├── core/          # Vision Gate, Anti-Loops
│   ├── design/        # Design task routing
│   ├── llm/           # LLM call rules
│   └── browser/       # Browser automation rules
├── configuration/     # Configuration files
├── tools/             # Tool documentation
├── MIGRATION.md       # Migration guide from AGENTS.md
└── EPIC_58_CHECKLIST.md # Epic completion checklist
```

## 🔒 Core Principles

1. **Vision Gate First** - Every web action requires a screenshot and vision check
2. **No Blind Actions** - Never click/type without visual confirmation
3. **Explicit Parameters** - No assumptions, always explicit configuration
4. **Chrome Profile Required** - Never use `user_data_dir=None`

## 📋 Quick Links

| Section | Description |
|---------|-------------|
| [Rules](./rules/README.md) | All operational rules |
| [Configuration](./configuration/models.md) | Model and plugin configuration |
| [Tools](./tools/look_at.md) | Tool documentation |
| [Migration Guide](./MIGRATION.md) | From AGENTS.md to modular docs |
