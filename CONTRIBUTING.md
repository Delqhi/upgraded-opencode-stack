# Contributing to Upgraded OpenCode Stack

Thank you for your interest! Here's how to contribute:

## Getting Started

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run `./install.sh` to verify the installer works
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
git clone https://github.com/Delqhi/upgraded-opencode-stack.git
cd upgraded-opencode-stack
```

> [!IMPORTANT]
> After any change to `opencode.json`, you MUST run `sin-sync` to sync across all machines.

## Code Style

- Shell scripts: Follow shellcheck guidelines
- Python scripts: PEP 8 compliant
- JSON configs: Valid JSON with 2-space indentation
- Add comments explaining complex logic

## Reporting Bugs

Please use [GitHub Issues](https://github.com/Delqhi/upgraded-opencode-stack/issues) with:

- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, OpenCode version, etc.)

## Pull Request Checklist

- [ ] Installer runs without errors (`./install.sh`)
- [ ] All new files have appropriate comments
- [ ] Documentation updated if needed
- [ ] No secrets or API keys committed
- [ ] Auth files are excluded from sync

> [!NOTE]
> Auth files (`auth.json`, `token.json`, `antigravity-accounts.json`, `telegram_config.json`) are NEVER synced and should NEVER be committed.
