from __future__ import annotations

import argparse
from pathlib import Path

from _flow_common import (
    ensure_state,
    resolve_root,
    save_json,
    slugify,
    write_flow_markdown,
    write_state,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--root", default=None)
    parser.add_argument("--description", default="")
    args = parser.parse_args()

    root = resolve_root(args.root)
    slug = slugify(args.name)
    state = ensure_state(args.name, slug, root, args.description)
    write_flow_markdown(root, slug, args.name, args.description)
    write_state(root, slug, state)
    print(str((root / ".opencode" / "flows" / slug).resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
