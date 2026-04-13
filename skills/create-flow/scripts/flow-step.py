from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from _flow_common import (
    append_brain,
    build_vision_prompt,
    capture_screenshot,
    ensure_state,
    feed_success,
    record_step,
    resolve_root,
    reset_incomplete_progress,
    run_vision_command,
    slugify,
    screenshot_dimensions,
    verdict_from_output,
    write_step_artifacts,
    write_state,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow", required=True)
    parser.add_argument("--root", default=None)
    parser.add_argument(
        "--level", default="run", choices=["run", "mini", "low", "high", "max", "full"]
    )
    parser.add_argument("--action", required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--note", default="")
    parser.add_argument("--vision-cmd", default=None)
    parser.add_argument(
        "--fast",
        action="store_true",
        help="High-Speed Anti-Bot Modus: skip vision checks",
    )
    args = parser.parse_args()

    root = resolve_root(args.root)
    slug = slugify(args.flow)
    state = ensure_state(args.flow, slug, root)

    base = root / ".opencode" / "flows" / slug
    evidence_root = base / "evidence"
    step_id = f"{args.level}-{len(state['steps']) + 1:04d}"
    step_dir = evidence_root / step_id
    step_dir.mkdir(parents=True, exist_ok=True)

    action_file = step_dir / "action.txt"
    action_file.write_text(args.action + "\n")

    subprocess.run(args.action, shell=True, check=True)

    screenshot_path = step_dir / "screenshot.png"
    capture_screenshot(screenshot_path)
    screenshot_size = screenshot_dimensions(screenshot_path)

    if args.fast:
        vision_output = "FAST MODE ACTIVE: Vision analysis skipped to maintain high-speed anti-bot execution."
        verdict = "PROCEED"
        prompt = build_vision_prompt(
            args.action, args.expected, args.note, screenshot_size=screenshot_size
        )
    else:
        prompt = build_vision_prompt(
            args.action, args.expected, args.note, screenshot_size=screenshot_size
        )
        vision_output = run_vision_command(screenshot_path, prompt, args.vision_cmd)
        verdict = verdict_from_output(vision_output)

    write_step_artifacts(
        step_dir,
        prompt,
        vision_output,
        verdict,
        screenshot_size=screenshot_size,
    )

    meta = {
        "step_id": step_id,
        "flow": args.flow,
        "slug": slug,
        "level": args.level,
        "action": args.action,
        "expected": args.expected,
        "note": args.note,
        "screenshot": str(screenshot_path),
        "analysis": str(step_dir / "analysis.md"),
        "screenshot_size": {
            "width": screenshot_size[0] if screenshot_size else None,
            "height": screenshot_size[1] if screenshot_size else None,
        },
        "vision": vision_output,
        "verdict": verdict,
    }
    (step_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n"
    )

    entry = record_step(
        state,
        step_id,
        args.level,
        args.action,
        args.expected,
        args.note,
        str(screenshot_path),
        vision_output,
        verdict,
    )

    if verdict == "PROCEED":
        promotions = feed_success(state, 0, [])
    else:
        reset_incomplete_progress(state)
        promotions = []

    state["promotions"].append(
        {
            "step_id": step_id,
            "verdict": verdict,
            "events": promotions,
        }
    )

    size_line = (
        f"- Screenshot size: `{screenshot_size[0]}x{screenshot_size[1]}`\n"
        if screenshot_size
        else "- Screenshot size: `unknown`\n"
    )

    append_brain(
        root,
        slug,
        f"## {step_id}\n- Action: {args.action}\n- Expected: {args.expected}\n- Verdict: {verdict}\n- Screenshot: {screenshot_path}\n{size_line}- Analysis: {step_dir / 'analysis.md'}\n- Vision:\n{vision_output}\n- Promotions: {json.dumps(promotions, ensure_ascii=False)}\n",
    )

    write_state(root, slug, state)

    print(
        json.dumps(
            {"step": entry, "verdict": verdict, "promotions": promotions},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if verdict == "PROCEED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
