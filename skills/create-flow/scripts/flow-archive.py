from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path

from _flow_common import archives_dir, ensure_state, flow_base, resolve_root, slugify


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow", required=True)
    parser.add_argument("--root", default=None)
    args = parser.parse_args()

    root = resolve_root(args.root)
    slug = slugify(args.flow)
    state = ensure_state(args.flow, slug, root)
    base = flow_base(root, slug)
    out_dir = archives_dir(root, slug)
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{slug}-evidence.tar.gz"

    with tarfile.open(archive, "w:gz") as handle:
        for rel in ["state.json", "brain.md", "flow.md", "evidence"]:
            path = base / rel
            if path.exists():
                handle.add(path, arcname=rel)

    print(
        json.dumps(
            {"archive": str(archive), "flow": state["flow"]["name"]},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
