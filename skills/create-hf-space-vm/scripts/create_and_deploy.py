#!/usr/bin/env python3
"""Create HF Space and deploy agent files in one command."""

import argparse
import json
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi, HfFolder


def get_token() -> str:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        return token
    cache_file = Path.home() / ".huggingface" / "token"
    if cache_file.exists():
        return cache_file.read_text().strip()
    token = HfFolder.get_token()
    if token:
        return token
    raise RuntimeError("No HF token found.")


def main():
    parser = argparse.ArgumentParser(description="Create HF Space and deploy agent")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--namespace", default="OpenJerro")
    parser.add_argument("--display-name")
    parser.add_argument("--description", default="")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--hardware", default="cpu-basic")
    parser.add_argument("--sleep-time", type=int, default=48)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    api = HfApi(token=get_token())
    repo_id = f"{args.namespace}/{args.slug}"

    status = {"repo_id": repo_id, "steps": []}

    try:
        api.space_info(repo_id)
        status["steps"].append({"step": "check", "status": "exists"})
        print(f"⚠️  Space exists: https://huggingface.co/spaces/{repo_id}")
    except Exception:
        api.create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="docker",
            space_hardware=args.hardware,
            space_sleep_time=args.sleep_time,
        )
        status["steps"].append({"step": "create", "status": "ok"})
        print(f"✅ Created: https://huggingface.co/spaces/{repo_id}")

    source = Path(args.source_dir)
    if source.exists():
        api.upload_folder(
            repo_id=repo_id,
            repo_type="space",
            folder_path=str(source),
            commit_message=f"Deploy {args.slug}",
        )
        status["steps"].append({"step": "deploy", "status": "ok"})
        print(f"✅ Deployed from {args.source_dir}")
    else:
        status["steps"].append(
            {"step": "deploy", "status": "skipped", "reason": "source not found"}
        )
        print(f"⚠️  Source not found: {args.source_dir}")

    status["url"] = f"https://huggingface.co/spaces/{repo_id}"

    if args.json:
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
