from __future__ import annotations

import argparse
import json

from _flow_common import (
    ensure_state,
    rebuild_promotions,
    resolve_root,
    slugify,
    write_state,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow", required=True)
    parser.add_argument("--root", default=None)
    args = parser.parse_args()

    root = resolve_root(args.root)
    slug = slugify(args.flow)
    state = ensure_state(args.flow, slug, root)
    events = rebuild_promotions(state)
    state["promotions"].append(
        {"step_id": "rebuild", "verdict": "PROCEED", "events": events}
    )
    write_state(root, slug, state)
    print(
        json.dumps(
            {"events": events, "progress": state["progress"]},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
