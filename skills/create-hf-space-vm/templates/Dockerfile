FROM node:22-slim

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev 2>/dev/null || npm install --omit=dev

COPY . .

RUN npm run build 2>/dev/null || true

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD node -e "require('http').get('http://localhost:7860/health', r => process.exit(r.statusCode === 200 ? 0 : 1))" || exit 1

CMD ["node", "dist/src/cli.js", "serve-a2a"]
