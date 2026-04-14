# Security — 7-Layer Hardening

Every agent MUST implement:
1. `.githooks/pre-commit` — Secret detection
2. `.githooks/pre-push` — Commit message leak detection
3. `.secrets.baseline` — detect-secrets
4. `governance/source-code-classification.md`
5. `governance/incident-response-playbook.md`
6. `.github/workflows/leak-prevention.yml`
7. Zero external code references (no claude/anthropic/@ant/)
