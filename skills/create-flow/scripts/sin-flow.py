#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import argparse
import json

from guard_create_flow import run_guard
from sin_flow_runtime import (
    archive_flow,
    create_flow_workspace,
    rebuild_flow_brain,
    run_flow_step,
    run_keyshot,
    status_text,
)


def _print_step(result: dict) -> None:
    step = result["step"]
    print(
        json.dumps(
            {
                "step_id": step["id"],
                "verdict": result["verdict"],
                "promotions": result["promotions"],
                "screenshot": result["screenshot"],
                "analysis": result.get("analysis"),
                "screenshot_size": result.get("step", {}).get("screenshot_size"),
                "vision_output": result.get("vision_output"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_record(args: argparse.Namespace) -> int:
    create_flow_workspace(args.flow, args.root, args.description)
    print(f"[flow] ready: {args.flow}")
    print("[flow] enter one action per run; empty action exits")
    while True:
        action = input("action> ").strip()
        if not action:
            break
        expected = input("expected> ").strip() or "action succeeded"
        note = input("note> ").strip()
        mode = input("mode [auto/shell/applescript/python]> ").strip() or "auto"
        result = run_flow_step(
            args.flow,
            action=action,
            expected=expected,
            note=note,
            root_arg=args.root,
            mode=mode,
            level=args.level,
            vision_cmd=args.vision_cmd,
        )
        _print_step(result)
        if result["verdict"] != "PROCEED" and not args.keep_going:
            retry = input("verdict not PROCEED; continue? [y/N]> ").strip().lower()
            if retry != "y":
                break
    return 0


def cmd_step(args: argparse.Namespace) -> int:
    create_flow_workspace(args.flow, args.root, args.description)
    result = run_flow_step(
        args.flow,
        action=args.action,
        expected=args.expected,
        note=args.note,
        root_arg=args.root,
        mode=args.mode,
        level=args.level,
        vision_cmd=args.vision_cmd,
        dry_run=args.dry_run,
        fast=args.fast,
    )
    _print_step(result)
    return 0 if result["verdict"] == "PROCEED" else 2


def cmd_keyshot(args: argparse.Namespace) -> int:
    create_flow_workspace(args.flow, args.root, args.description)
    result = run_keyshot(
        args.flow,
        expected=args.expected,
        note=args.note,
        root_arg=args.root,
        vision_cmd=args.vision_cmd,
        level=args.level,
    )
    _print_step(result)
    return 0 if result["verdict"] == "PROCEED" else 2


def cmd_status(args: argparse.Namespace) -> int:
    create_flow_workspace(args.flow, args.root, args.description)
    print(status_text(args.flow, root_arg=args.root))
    return 0


def cmd_brain(args: argparse.Namespace) -> int:
    create_flow_workspace(args.flow, args.root, args.description)
    result = rebuild_flow_brain(args.flow, root_arg=args.root)
    print(
        json.dumps(
            {"brain": result["brain"], "events": result["events"]},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    return cmd_brain(args)


def cmd_archive(args: argparse.Namespace) -> int:
    create_flow_workspace(args.flow, args.root, args.description)
    result = archive_flow(args.flow, root_arg=args.root)
    print(json.dumps({"archive": result["archive"]}, indent=2, ensure_ascii=False))
    return 0


def cmd_guard(args: argparse.Namespace) -> int:
    report = run_guard(args.repo)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 2


def cmd_init(args: argparse.Namespace) -> int:
    result = create_flow_workspace(args.flow, args.root, args.description)
    print(
        json.dumps(
            {"flow": args.flow, "slug": result["slug"], "root": result["root"]},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _load_batch(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text())
        if not isinstance(data, list):
            raise ValueError("batch JSON must be a list")
        return [
            {
                "mode": item.get("mode", "auto"),
                "action": item["action"],
                "expected": item.get("expected", "action succeeded"),
                "note": item.get("note", ""),
                "level": item.get("level", "run"),
            }
            for item in data
        ]
    items: list[dict[str, str]] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        while len(parts) < 4:
            parts.append("")
        items.append(
            {
                "mode": parts[0] or "auto",
                "action": parts[1],
                "expected": parts[2] or "action succeeded",
                "note": parts[3],
                "level": "run",
            }
        )
    return items


def cmd_batch(args: argparse.Namespace) -> int:
    create_flow_workspace(args.flow, args.root, args.description)
    items = _load_batch(Path(args.file))
    for idx, item in enumerate(items, start=1):
        result = run_flow_step(
            args.flow,
            action=item["action"],
            expected=item["expected"],
            note=item["note"],
            root_arg=args.root,
            mode=item["mode"],
            level=item["level"],
            vision_cmd=args.vision_cmd,
        )
        print(f"[{idx}/{len(items)}] {item['action']} => {result['verdict']}")
        if result["verdict"] != "PROCEED" and not args.keep_going:
            return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sin-flow", description="Blitz-fast flow builder"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("flow")
    shared.add_argument("--root", default=None)
    shared.add_argument("--description", default="")
    shared.add_argument("--vision-cmd", default=None)

    p = sub.add_parser("record", parents=[shared], help="interactive record mode")
    p.add_argument("--level", default="run")
    p.add_argument("--keep-going", action="store_true")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("step", parents=[shared], help="execute one action")
    p.add_argument("--action", required=True)
    p.add_argument("--expected", required=True)
    p.add_argument("--note", default="")
    p.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "shell", "applescript", "python", "nodriver"],
    )
    p.add_argument("--level", default="run")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--fast",
        action="store_true",
        help="High-Speed Anti-Bot Modus: skip vision checks",
    )
    p.set_defaults(func=cmd_step)

    p = sub.add_parser(
        "keyshot", parents=[shared], help="capture screenshot + vision only"
    )
    p.add_argument("--expected", required=True)
    p.add_argument("--note", default="")
    p.add_argument("--level", default="run")
    p.set_defaults(func=cmd_keyshot)

    p = sub.add_parser("status", parents=[shared], help="show flow status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("brain", parents=[shared], help="rebuild brain from state")
    p.set_defaults(func=cmd_brain)

    p = sub.add_parser("promote", parents=[shared], help="recompute promotion ladder")
    p.set_defaults(func=cmd_promote)

    p = sub.add_parser("archive", parents=[shared], help="bundle evidence archive")
    p.set_defaults(func=cmd_archive)

    p = sub.add_parser("guard", help="detect divergent create-flow runtimes")
    p.add_argument("--repo", default=".")
    p.set_defaults(func=cmd_guard)

    p = sub.add_parser("batch", parents=[shared], help="run a file of single actions")
    p.add_argument("--file", required=True)
    p.add_argument("--keep-going", action="store_true")
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("init", parents=[shared], help="create flow workspace")
    p.set_defaults(func=cmd_init)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
