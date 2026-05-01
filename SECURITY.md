# Security Policy

## Supported Versions

| Version       | Supported |
| :------------ | :-------- |
| main (latest) | ✅        |
| < main        | ❌        |

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **DO NOT** open a public issue
2. Email us at: security@example.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to resolve the issue.

## Security Best Practices

- **NEVER** commit auth files (`auth.json`, `token.json`, `antigravity-accounts.json`)
- **NEVER** commit API keys or secrets
- Use environment variables for configuration
- Review all PRs for security implications
- Keep dependencies updated
- The `sin-sync` script automatically excludes auth files from synchronization

## Excluded from Sync (Never Transmitted)

- `auth.json`, `token.json` — API tokens
- `antigravity-accounts.json` — OAuth accounts
- `telegram_config.json` — Telegram bot config
- `*_cookies.json` — Browser cookies
- `*.db`, `*.sqlite*` — Local databases
- `node_modules/` — Package dependencies
