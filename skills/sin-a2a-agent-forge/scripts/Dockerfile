FROM node:22-slim

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --omit=dev 2>/dev/null || npm install

# Copy source
COPY . .

# Build if needed
RUN npm run build 2>/dev/null || true

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

# Start
CMD ["node", "server.js"]
