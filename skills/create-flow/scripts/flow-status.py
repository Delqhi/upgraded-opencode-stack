from __future__ import annotations

import argparse
import json

from _flow_common import ensure_state, flow_summary, resolve_root, slugify


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow", required=True)
    parser.add_argument("--root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = resolve_root(args.root)
    slug = slugify(args.flow)
    state = ensure_state(args.flow, slug, root)

    if args.json:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        print(flow_summary(state))
        print(f"steps={len(state.get('steps', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
