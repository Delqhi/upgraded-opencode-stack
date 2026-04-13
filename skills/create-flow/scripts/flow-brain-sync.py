from __future__ import annotations

import argparse
import json

from _flow_common import brain_path, ensure_state, resolve_root, slugify, write_state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow", required=True)
    parser.add_argument("--root", default=None)
    args = parser.parse_args()

    root = resolve_root(args.root)
    slug = slugify(args.flow)
    state = ensure_state(args.flow, slug, root)
    path = brain_path(root, slug)

    lines = [
        f"# Flow Brain: {state['flow']['name']}",
        "",
        "## Progress",
        "",
    ]
    for level, progress in state["progress"].items():
        lines.append(
            f"- {level}: pair={progress['pair_buffer']} candidate={progress['candidate_streak']} approved_units={progress['approved_units']} approved={progress['approved']}"
        )
    lines.extend(["", "## Steps", ""])
    for step in state.get("steps", []):
        lines.append(
            f"- {step['id']} | {step['level']} | {step['verdict']} | {step['action']} | {step['screenshot']} | {step.get('analysis', '')}"
        )
    path.write_text("\n".join(lines) + "\n")
    write_state(root, slug, state)
    print(
        json.dumps(
            {"brain": str(path), "steps": len(state.get("steps", []))},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
