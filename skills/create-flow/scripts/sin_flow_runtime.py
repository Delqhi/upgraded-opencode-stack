from __future__ import annotations

import json
import subprocess
import tarfile
from pathlib import Path
from typing import Any

from _flow_common import (
    append_brain,
    archives_dir,
    build_vision_prompt,
    capture_screenshot,
    evidence_dir,
    ensure_layout,
    ensure_state,
    feed_success,
    flow_base,
    flow_markdown_path,
    flow_summary,
    record_step,
    rebuild_promotions,
    resolve_root,
    reset_incomplete_progress,
    run_vision_command,
    save_json,
    slugify,
    state_path,
    screenshot_dimensions,
    verdict_from_output,
    write_step_artifacts,
    write_flow_markdown,
    write_state,
)


def execute_action(action: str, mode: str = "auto") -> None:
    if not action:
        return
    if mode == "auto":
        if action.lstrip().startswith("tell "):
            mode = "applescript"
        else:
            mode = "shell"
    if mode == "applescript":
        subprocess.run(["osascript", "-e", action], check=True)
        return
    if mode == "python":
        subprocess.run(["python3", "-c", action], check=True)
        return
    subprocess.run(action, shell=True, check=True)


def create_flow_workspace(
    flow_name: str, root_arg: str | None = None, description: str = ""
) -> dict[str, Any]:
    root = resolve_root(root_arg)
    slug = slugify(flow_name)
    state = ensure_state(flow_name, slug, root, description)
    write_flow_markdown(root, slug, flow_name, description)
    write_state(root, slug, state)
    return {"root": str(flow_base(root, slug)), "slug": slug, "state": state}


def run_flow_step(
    flow_name: str,
    action: str,
    expected: str,
    note: str = "",
    *,
    root_arg: str | None = None,
    mode: str = "auto",
    level: str = "run",
    vision_cmd: str | None = None,
    dry_run: bool = False,
    keyshot_only: bool = False,
) -> dict[str, Any]:
    root = resolve_root(root_arg)
    slug = slugify(flow_name)
    state = ensure_state(flow_name, slug, root, note)
    base = ensure_layout(root, slug)
    step_index = len(state.get("steps", [])) + 1
    step_id = f"{level}-{step_index:04d}"
    step_dir = evidence_dir(root, slug) / step_id
    step_dir.mkdir(parents=True, exist_ok=True)

    if not keyshot_only and action and not dry_run:
        execute_action(action, mode=mode)

    screenshot_path = step_dir / "screenshot.png"
    capture_screenshot(screenshot_path)
    screenshot_size = screenshot_dimensions(screenshot_path)
    prompt = build_vision_prompt(
        action or "keyshot", expected, note, screenshot_size=screenshot_size
    )
    vision_output = run_vision_command(screenshot_path, prompt, vision_cmd=vision_cmd)
    verdict = verdict_from_output(vision_output)
    write_step_artifacts(
        step_dir, prompt, vision_output, verdict, screenshot_size=screenshot_size
    )

    entry = record_step(
        state,
        step_id,
        level,
        action,
        expected,
        note,
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
        {"step_id": step_id, "verdict": verdict, "events": promotions}
    )
    size_line = (
        f"- Screenshot size: `{screenshot_size[0]}x{screenshot_size[1]}`\n"
        if screenshot_size
        else "- Screenshot size: `unknown`\n"
    )
    append_brain(
        root,
        slug,
        (
            f"## {step_id}\n"
            f"- Action: `{action}`\n"
            f"- Expected: {expected}\n"
            f"- Verdict: **{verdict}**\n"
            f"- Screenshot: `{screenshot_path}`\n"
            f"{size_line}"
            f"- Analysis: `{step_dir / 'analysis.md'}`\n"
            f"- Vision: {vision_output}\n"
            f"- Promotions: {json.dumps(promotions, ensure_ascii=False)}\n"
        ),
    )
    write_state(root, slug, state)
    return {
        "flow": flow_name,
        "slug": slug,
        "step": entry,
        "verdict": verdict,
        "promotions": promotions,
        "state": state,
        "screenshot": str(screenshot_path),
        "analysis": str(step_dir / "analysis.md"),
        "screenshot_size": {
            "width": screenshot_size[0] if screenshot_size else None,
            "height": screenshot_size[1] if screenshot_size else None,
        },
        "vision_output": vision_output,
    }


def run_keyshot(
    flow_name: str,
    expected: str,
    note: str = "",
    *,
    root_arg: str | None = None,
    vision_cmd: str | None = None,
    level: str = "run",
) -> dict[str, Any]:
    return run_flow_step(
        flow_name,
        action="",
        expected=expected,
        note=note,
        root_arg=root_arg,
        mode="auto",
        level=level,
        vision_cmd=vision_cmd,
        dry_run=True,
        keyshot_only=True,
    )


def rebuild_flow_brain(
    flow_name: str, *, root_arg: str | None = None
) -> dict[str, Any]:
    root = resolve_root(root_arg)
    slug = slugify(flow_name)
    state = ensure_state(flow_name, slug, root)
    events = rebuild_promotions(state)
    path = flow_base(root, slug) / "brain.md"
    progress_lines = [
        f"- {level}: pair={progress['pair_buffer']} candidate={progress['candidate_streak']} approved_units={progress['approved_units']} approved={progress['approved']}"
        for level, progress in state["progress"].items()
    ]
    step_lines = [
        f"- {step['id']} | {step['level']} | {step['verdict']} | {step['action']} | {step['screenshot']} | {step.get('analysis', '')}"
        for step in state.get("steps", [])
    ]
    path.write_text(
        "\n".join(
            [
                f"# Flow Brain: {flow_name}",
                "",
                "## Progress",
                "",
                *progress_lines,
                "",
                "## Steps",
                "",
                *step_lines,
                "",
            ]
        )
    )
    write_state(root, slug, state)
    return {"brain": str(path), "events": events, "state": state}


def archive_flow(flow_name: str, *, root_arg: str | None = None) -> dict[str, Any]:
    root = resolve_root(root_arg)
    slug = slugify(flow_name)
    state = ensure_state(flow_name, slug, root)
    base = flow_base(root, slug)
    out_dir = archives_dir(root, slug)
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{slug}-evidence.tar.gz"
    with tarfile.open(archive, "w:gz") as handle:
        for rel in ["state.json", "brain.md", "flow.md", "evidence"]:
            path = base / rel
            if path.exists():
                handle.add(path, arcname=rel)
    return {"archive": str(archive), "state": state}


def status_text(flow_name: str, *, root_arg: str | None = None) -> str:
    root = resolve_root(root_arg)
    slug = slugify(flow_name)
    state = ensure_state(flow_name, slug, root)
    return flow_summary(state)
