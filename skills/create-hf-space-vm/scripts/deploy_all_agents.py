#!/usr/bin/env python3
"""Deploy all 8 platform agents to their HF Spaces."""

import os
import sys
from pathlib import Path
from huggingface_hub import HfApi

HF_TOKEN = os.environ.get("HF_TOKEN", "YOUR_HF_TOKEN_HERE")
NAMESPACE = "OpenJerro"
MONOREPO = "/Users/jeremy/dev/OpenSIN-monorepo/a2a/team-marketing"

AGENTS = [
    "A2A-SIN-Reddit",
    "A2A-SIN-Discord",
    "A2A-SIN-YouTube",
    "A2A-SIN-TikTok",
    "A2A-SIN-Medium",
    "A2A-SIN-Instagram",
    "A2A-SIN-X-Twitter",
    "A2A-SIN-Community",
]

SLUG_MAP = {
    "A2A-SIN-Reddit": "sin-reddit",
    "A2A-SIN-Discord": "sin-discord",
    "A2A-SIN-YouTube": "sin-youtube",
    "A2A-SIN-TikTok": "sin-tiktok",
    "A2A-SIN-Medium": "sin-medium",
    "A2A-SIN-Instagram": "sin-instagram",
    "A2A-SIN-X-Twitter": "sin-x-twitter",
    "A2A-SIN-Community": "sin-community",
}

DOCKERFILE = """FROM node:22-slim

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev 2>/dev/null || npm install --omit=dev

COPY . .

RUN npm run build 2>/dev/null || true

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
  CMD node -e "require('http').get('http://localhost:7860/health', r => process.exit(r.statusCode === 200 ? 0 : 1))" || exit 1

CMD ["node", "dist/src/cli.js", "serve-a2a"]
"""

APP_PY = """import gradio as gr

def greet(name):
    return f"SIN Agent running. Connect via A2A protocol at /a2a/v1"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")
demo.launch(server_name="0.0.0.0", server_port=7860)
"""

REQUIREMENTS = "gradio\nhuggingface_hub\n"


def main():
    api = HfApi(token=HF_TOKEN)

    for agent_dir in AGENTS:
        slug = SLUG_MAP[agent_dir]
        repo_id = f"{NAMESPACE}/{slug}"
        source = Path(MONOREPO) / agent_dir

        if not source.exists():
            print(f"❌ {agent_dir}: source not found at {source}")
            continue

        files_to_upload = {
            "Dockerfile": DOCKERFILE,
            "app.py": APP_PY,
            "requirements.txt": REQUIREMENTS,
        }

        for filename, content in files_to_upload.items():
            api.upload_file(
                path_or_fileobj=content.encode(),
                path_in_repo=filename,
                repo_id=repo_id,
                repo_type="space",
                commit_message=f"Add {filename} for {slug}",
            )

        print(f"✅ Deployed Dockerfile, app.py, requirements.txt to {repo_id}")


if __name__ == "__main__":
    main()
