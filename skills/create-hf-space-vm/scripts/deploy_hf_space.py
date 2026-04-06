#!/usr/bin/env python3
"""Deploy files to an existing HF Space."""

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


def deploy_files(
    api: HfApi,
    slug: str,
    namespace: str,
    source_dir: str,
    files: list = None,
    commit_message: str = None,
) -> dict:
    repo_id = f"{namespace}/{slug}"
    source = Path(source_dir)

    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    upload_files = []
    if files:
        for f in files:
            path = source / f
            if path.exists():
                upload_files.append((f, str(path)))
    else:
        for path in source.rglob("*"):
            if path.is_file():
                rel = path.relative_to(source)
                rel_str = str(rel)
                if rel_str.startswith(".git") or rel_str.startswith("node_modules"):
                    continue
                upload_files.append((rel_str, str(path)))

    api.upload_folder(
        repo_id=repo_id,
        repo_type="space",
        folder_path=str(source),
        commit_message=commit_message or f"Deploy {slug}",
    )

    url = f"https://huggingface.co/spaces/{repo_id}"
    print(f"✅ Deployed {len(upload_files)} files to {url}")
    return {"repo_id": repo_id, "url": url, "files_deployed": len(upload_files)}


def main():
    parser = argparse.ArgumentParser(description="Deploy files to HF Space")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--namespace", default="OpenJerro")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--files", nargs="*")
    parser.add_argument("--commit-message", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    api = HfApi(token=get_token())
    result = deploy_files(
        api, args.slug, args.namespace, args.source_dir, args.files, args.commit_message
    )

    if args.json:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
