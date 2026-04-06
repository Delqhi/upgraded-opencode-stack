FROM node:20-alpine

# Install system dependencies
RUN apk add --no-cache \
    curl \
    git \
    python3 \
    py3-pip \
    sqlite \
    ffmpeg \
    jq \
    tree \
    htop \
    ripgrep \
    nodejs \
    npm \
    bash \
    github-cli \
    make \
    gcc \
    g++ \
    python3-dev

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash

# Install npm global tools
RUN npm install -g wrangler @google/gemini-cli

# Install yq
RUN wget https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -O /usr/local/bin/yq && \
    chmod +x /usr/local/bin/yq

# Clone upgraded-opencode-stack repo
RUN git clone https://github.com/Delqhi/upgraded-opencode-stack.git /opt/upgraded-opencode-stack

# Set environment
ENV PATH="/root/.bun/bin:/usr/local/bin:$PATH"

# Default command
CMD ["opencode"]