from __future__ import annotations

import argparse
import json
from pathlib import Path

RUNTIME_FILE_NAMES = {
    "_flow_common.py",
    "create-flow.py",
    "flow-archive.py",
    "flow-brain-sync.py",
    "flow-status.py",
    "flow-promote.py",
    "flow-step.py",
    "flow_cdp_utils.py",
    "guard_create_flow.py",
    "sin-flow.py",
    "sin-flowd.py",
    "sin_flow_runtime.py",
}

CANONICAL_LAYOUTS = {
    "SIN-InkogniFlow": {Path("opencode/skills/create-flow")},
    "upgraded-opencode-stack": {Path("skills/create-flow")},
}

SKIP_PARTS = {
    ".git",
    ".next",
    ".opencode",
    ".pcpm",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "venv",
}


def is_skipped(relative_path: Path) -> bool:
    return any(part in SKIP_PARTS for part in relative_path.parts)


def allowed_prefixes(repo_name: str) -> tuple[Path, ...]:
    return tuple(CANONICAL_LAYOUTS.get(repo_name, set()))


def is_allowed_path(repo_name: str, relative_path: Path) -> bool:
    return any(relative_path == prefix or relative_path.is_relative_to(prefix) for prefix in allowed_prefixes(repo_name))


def looks_like_runtime_file(relative_path: Path) -> bool:
    if relative_path.name in RUNTIME_FILE_NAMES:
        return True
    return relative_path.name == "SKILL.md" and "create-flow" in relative_path.parts


def collect_violations(repo_root: Path) -> list[dict[str, str]]:
    repo_name = repo_root.name
    violations: list[dict[str, str]] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(repo_root)
        if is_skipped(relative_path):
            continue
        if is_allowed_path(repo_name, relative_path):
            continue
        if looks_like_runtime_file(relative_path):
            violations.append(
                {
                    "path": relative_path.as_posix(),
                    "reason": "divergent create-flow runtime artifact outside canonical layout",
                }
            )
    return violations


def run_guard(repo_root: str | Path | None = None) -> dict:
    resolved_root = Path(repo_root or Path.cwd()).expanduser().resolve()
    repo_name = resolved_root.name
    report = {
        "repo": str(resolved_root),
        "repo_name": repo_name,
        "allowed_prefixes": [prefix.as_posix() for prefix in allowed_prefixes(repo_name)],
        "violations": collect_violations(resolved_root),
    }
    report["ok"] = not report["violations"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    report = run_guard(args.repo)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
