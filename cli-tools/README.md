# CLI Tools Installation Guide

This directory contains installation commands for all essential CLI tools used in the upgraded OpenCode stack development environment.

## Core System Tools

### Homebrew (Package Manager)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Git

```bash
brew install git
```

### Curl

```bash
# Already installed on macOS
```

### Zsh/Bash

```bash
# Already installed on macOS
```

## Development Runtimes

### Node.js (via nvm)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
# Then: nvm install node && nvm use node
```

### Bun

```bash
curl -fsSL https://bun.sh/install | bash
```

### Python

```bash
brew install python
```

## Container & Virtualization

### Docker Desktop

```bash
# Download from: https://www.docker.com/products/docker-desktop
# Install the .dmg file
```

## OpenCode & AI Tools

### OpenCode CLI

```bash
# From source:
git clone https://github.com/anomalyco/opencode.git
cd opencode
bun install
bun run build
cp bin/opencode ~/.opencode/bin/
chmod +x ~/.opencode/bin/opencode

# Or via Docker:
docker pull ghcr.io/anomalyco/opencode:latest
```

### Wrangler CLI (Cloudflare)

```bash
npm install -g wrangler
```

### GitHub CLI

```bash
brew install gh
```

### Gemini CLI

```bash
npm install -g @google/gemini-cli
```

## Database Tools

### SQLite

```bash
brew install sqlite
```

## Additional Tools

### FFmpeg

```bash
brew install ffmpeg
```

### Ripgrep

```bash
brew install ripgrep
```

### Tree

```bash
brew install tree
```

### htop

```bash
brew install htop
```

### jq (JSON processor)

```bash
brew install jq
```

### yq (YAML processor)

```bash
brew install yq
```

## Installation Script

To install all tools automatically, run:

```bash
# Install Homebrew first
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install all tools
brew install git python sqlite ffmpeg ripgrep tree htop jq yq gh

# Install Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.zshrc
nvm install node
nvm use node

# Install Bun
curl -fsSL https://bun.sh/install | bash

# Install CLI tools
npm install -g wrangler @google/gemini-cli
```

## Docker Integration

For Docker containers, add these tools to your Dockerfile:

```dockerfile
FROM node:18-alpine

# Install additional tools
RUN apk add --no-cache git curl python3 sqlite ffmpeg ripgrep tree htop jq yq

# Install Node.js CLIs
RUN npm install -g wrangler @google/gemini-cli

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash

# Copy OpenCode binary
COPY opencode /usr/local/bin/opencode
```

## Notes

- All tools are installed globally for system-wide access
- Docker Desktop must be installed manually via GUI
- Some tools require sudo for system-level installation
- Restart terminal after installation to update PATH
