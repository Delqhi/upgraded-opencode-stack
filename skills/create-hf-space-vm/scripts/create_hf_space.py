#!/usr/bin/env python3
"""
Create Hugging Face Space VMs for A2A agents.
Deterministic, idempotent, zero-config.

Usage:
  python3 create_hf_space.py --slug sin-my-agent --namespace OpenJerro
  python3 create_hf_space.py --slug sin-my-agent --namespace OpenJerro --check-status
  python3 create_hf_space.py --namespace OpenJerro --list
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from huggingface_hub import HfApi, HfFolder
except ImportError:
    print("ERROR: huggingface_hub not installed. Run: pip install huggingface_hub")
    sys.exit(1)


def get_token() -> str:
    """Resolve HF token from multiple sources."""
    # 1. Environment variable
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        return token

    # 2. Local cache file
    cache_file = Path.home() / ".huggingface" / "token"
    if cache_file.exists():
        return cache_file.read_text().strip()

    # 3. macOS Keychain
    try:
        import subprocess

        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                "sin.passwordmanager",
                "-a",
                "secret:HUGGINGFACE_TOKEN",
                "-w",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    # 4. huggingface_hub login state
    token = HfFolder.get_token()
    if token:
        return token

    raise RuntimeError(
        "No HF token found. Set HF_TOKEN env var, create ~/.huggingface/token, "
        "or run `hf auth login`."
    )


def get_api() -> HfApi:
    """Create HfApi instance with resolved token."""
    return HfApi(token=get_token())


def check_status(api: HfApi, slug: str, namespace: str) -> dict:
    """Check if a Space exists and return its status."""
    repo_id = f"{namespace}/{slug}"
    try:
        info = api.space_info(repo_id)
        return {
            "exists": True,
            "repo_id": repo_id,
            "url": f"https://huggingface.co/spaces/{repo_id}",
            "sdk": info.sdk,
            "hardware": info.hardware,
            "stage": info.stage,
            "sleep_time": getattr(info, "sleep_time", None),
        }
    except Exception:
        return {"exists": False, "repo_id": repo_id}


def create_space(
    api: HfApi,
    slug: str,
    namespace: str,
    display_name: str = None,
    description: str = "",
    hardware: str = "cpu-basic",
    sleep_time: int = 48,
) -> dict:
    """Create a new HF Space or return existing info."""
    repo_id = f"{namespace}/{slug}"

    # Check if exists
    status = check_status(api, slug, namespace)
    if status["exists"]:
        print(f"⚠️  Space already exists: {status['url']}")
        return status

    # Create
    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="docker",
        space_hardware=hardware,
        space_sleep_time=sleep_time,
    )

    # Set title and description if provided
    if display_name or description:
        api.update_repo_settings(
            repo_id=repo_id,
            repo_type="space",
            title=display_name or slug,
            description=description,
        )

    url = f"https://huggingface.co/spaces/{repo_id}"
    print(f"✅ Created: {url}")
    return {
        "exists": True,
        "repo_id": repo_id,
        "url": url,
        "sdk": "docker",
        "hardware": hardware,
        "stage": "BUILDING",
    }


def list_spaces(api: HfApi, namespace: str) -> list:
    """List all Spaces for a namespace."""
    spaces = list(api.list_spaces(author=namespace))
    result = []
    for s in spaces:
        info = {
            "id": s.id,
            "url": f"https://huggingface.co/spaces/{s.id}",
            "sdk": s.sdk,
        }
        result.append(info)
        print(f"  {s.id} - SDK: {s.sdk}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Create HF Space VMs for A2A agents")
    parser.add_argument("--slug", help="Space slug (e.g., sin-reddit)")
    parser.add_argument("--namespace", default="OpenJerro", help="HF namespace")
    parser.add_argument("--display-name", help="Display name for the Space")
    parser.add_argument("--description", default="", help="Space description")
    parser.add_argument(
        "--hardware",
        default="cpu-basic",
        choices=[
            "cpu-basic",
            "cpu-upgrade",
            "gpu-t4-small",
            "gpu-t4-medium",
            "gpu-l4x1",
        ],
        help="Hardware tier",
    )
    parser.add_argument(
        "--sleep-time",
        type=int,
        default=48,
        help="Sleep timeout in hours (default: 48)",
    )
    parser.add_argument(
        "--check-status",
        action="store_true",
        help="Check if Space exists without creating",
    )
    parser.add_argument(
        "--list", action="store_true", help="List all Spaces for namespace"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    api = get_api()

    if args.list:
        spaces = list_spaces(api, args.namespace)
        if args.json:
            print(json.dumps(spaces, indent=2))
        return

    if not args.slug:
        parser.error("--slug is required (unless --list)")

    if args.check_status:
        status = check_status(api, args.slug, args.namespace)
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            if status["exists"]:
                print(f"✅ Exists: {status['url']}")
                print(f"   SDK: {status.get('sdk', '?')}")
                print(f"   Hardware: {status.get('hardware', '?')}")
                print(f"   Stage: {status.get('stage', '?')}")
            else:
                print(f"❌ Does not exist: {status['repo_id']}")
        return

    result = create_space(
        api,
        args.slug,
        args.namespace,
        display_name=args.display_name,
        description=args.description,
        hardware=args.hardware,
        sleep_time=args.sleep_time,
    )

    if args.json:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
