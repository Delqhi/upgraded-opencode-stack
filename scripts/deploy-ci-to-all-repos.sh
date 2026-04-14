#!/bin/bash
# Deploy CI workflow to all OpenSIN-AI repos
# Requires: gh CLI authenticated with repo scope

CONTENT=$(base64 -w0 << 'EOF'
name: CI to n8n OCI Runner

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  dispatch:
    name: Dispatch to n8n
    runs-on: ubuntu-latest
    timeout-minutes: 2
    steps:
      - uses: OpenSIN-AI/sin-github-action@main
        with:
          n8n_webhook_url: \${{ secrets.N8N_CI_WEBHOOK_URL }}
          github_token: \${{ secrets.GITHUB_TOKEN }}
          pipeline: all
EOF
)

REPOS=(
  "OpenSIN-AI/OpenSIN-backend"
  "OpenSIN-AI/OpenSIN-Neural-Bus"
  "OpenSIN-AI/Template-SIN-Agent"
  "OpenSIN-AI/Template-SIN-Team"
  "OpenSIN-AI/Team-SIN-Infrastructure"
  "OpenSIN-AI/Team-SIN-Code-Core"
  "OpenSIN-AI/Team-SIN-Code-Backend"
  "OpenSIN-AI/Team-SIN-Code-Frontend"
  "OpenSIN-AI/Team-SIN-Code-CyberSec"
)

for repo in "\${REPOS[@]}"; do
  gh api "repos/\$repo/contents/.github/workflows/ci.yml" \
    --method PUT \
    -f message="ci: use A2A-SIN-GitHub-Action + n8n instead of GitHub Actions" \
    -f content="\$CONTENT" \
    --jq '.commit.sha' 2>/dev/null && echo "✅ \$repo" || echo "❌ \$repo"
  sleep 1
done
