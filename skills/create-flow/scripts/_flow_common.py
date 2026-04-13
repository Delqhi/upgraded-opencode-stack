from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEVELS = ["run", "mini", "low", "high", "max", "full"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "flow"


def resolve_root(root_arg: str | None) -> Path:
    if root_arg:
        return Path(root_arg).expanduser().resolve()

    for env_name in ("CREATE_FLOW_ROOT", "FLOW_ROOT", "OPENCODE_PROJECT_ROOT"):
        env_value = os.environ.get(env_name)
        if env_value:
            return Path(env_value).expanduser().resolve()

    cwd = Path.cwd().resolve()
    git_root = detect_git_root(cwd)
    return git_root or cwd


def detect_git_root(start: Path) -> Path | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        root = (proc.stdout or "").strip()
        return Path(root).resolve() if root and proc.returncode == 0 else None
    except Exception:
        return None


def flow_base(root: Path, slug: str) -> Path:
    return root / ".opencode" / "flows" / slug


def state_path(root: Path, slug: str) -> Path:
    return flow_base(root, slug) / "state.json"


def brain_path(root: Path, slug: str) -> Path:
    return flow_base(root, slug) / "brain.md"


def flow_markdown_path(root: Path, slug: str) -> Path:
    return flow_base(root, slug) / "flow.md"


def evidence_dir(root: Path, slug: str) -> Path:
    return flow_base(root, slug) / "evidence"


def archives_dir(root: Path, slug: str) -> Path:
    return flow_base(root, slug) / "archives"


def ensure_layout(root: Path, slug: str) -> Path:
    base = flow_base(root, slug)
    (base / "evidence").mkdir(parents=True, exist_ok=True)
    (base / "archives").mkdir(parents=True, exist_ok=True)
    return base


def initial_state(
    flow_name: str, slug: str, root: Path, description: str
) -> dict[str, Any]:
    progress = {
        level: {
            "pair_buffer": 0,
            "candidate_streak": 0,
            "approved_units": 0,
            "approved": False,
        }
        for level in LEVELS
    }
    progress["full"]["approved"] = False
    return {
        "flow": {
            "name": flow_name,
            "slug": slug,
            "root": str(root),
            "description": description,
            "created_at": now(),
            "updated_at": now(),
        },
        "progress": progress,
        "steps": [],
        "promotions": [],
    }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def ensure_state(
    flow_name: str, slug: str, root: Path, description: str = ""
) -> dict[str, Any]:
    base = ensure_layout(root, slug)
    state_file = base / "state.json"
    if state_file.exists():
        state = load_json(state_file)
        state.setdefault("progress", {})
        state.setdefault("steps", [])
        state.setdefault("promotions", [])
        for level in LEVELS:
            state["progress"].setdefault(
                level,
                {
                    "pair_buffer": 0,
                    "candidate_streak": 0,
                    "approved_units": 0,
                    "approved": False,
                },
            )
        return state
    state = initial_state(flow_name, slug, root, description)
    save_json(state_file, state)
    return state


def write_state(root: Path, slug: str, state: dict[str, Any]) -> None:
    state["flow"]["updated_at"] = now()
    save_json(state_path(root, slug), state)


def write_flow_markdown(
    root: Path, slug: str, flow_name: str, description: str
) -> None:
    path = flow_markdown_path(root, slug)
    path.write_text(
        f"# {flow_name}\n\n"
        f"Slug: `{slug}`\n\n"
        f"Description: {description or 'Flow scaffold'}\n\n"
        "Rules:\n"
        "- one action per run\n"
        "- screenshot after each action\n"
        "- vision verdict after each screenshot\n"
        "- append evidence to the local brain\n"
        "- promote only after proof\n"
    )


def append_brain(root: Path, slug: str, text: str) -> None:
    path = brain_path(root, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text.rstrip() + "\n")


def capture_screenshot(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["screencapture", "-x", str(output_path)], check=True)


def screenshot_dimensions(screenshot_path: Path) -> tuple[int, int] | None:
    try:
        proc = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(screenshot_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        width_match = re.search(r"pixelWidth:\s*(\d+)", proc.stdout or "")
        height_match = re.search(r"pixelHeight:\s*(\d+)", proc.stdout or "")
        if not width_match or not height_match:
            return None
        return int(width_match.group(1)), int(height_match.group(1))
    except Exception:
        return None


def write_step_artifacts(
    step_dir: Path,
    prompt: str,
    vision_output: str,
    verdict: str,
    screenshot_size: tuple[int, int] | None = None,
) -> None:
    step_dir.mkdir(parents=True, exist_ok=True)
    size_line = (
        f"- Screenshot size: `{screenshot_size[0]}x{screenshot_size[1]}`\n"
        if screenshot_size
        else "- Screenshot size: `unknown`\n"
    )
    (step_dir / "vision.txt").write_text(
        vision_output.rstrip() + "\n", encoding="utf-8"
    )
    (step_dir / "analysis.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "screenshot_size": {
                    "width": screenshot_size[0] if screenshot_size else None,
                    "height": screenshot_size[1] if screenshot_size else None,
                },
                "prompt": prompt,
                "vision_output": vision_output,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (step_dir / "analysis.md").write_text(
        f"# Vision Analysis\n\n"
        f"## Metadata\n\n"
        f"- Verdict: `{verdict}`\n"
        f"{size_line}\n"
        f"## Prompt\n\n```text\n{prompt}\n```\n\n"
        f"## Raw Output\n\n{vision_output}\n",
        encoding="utf-8",
    )


def build_vision_prompt(
    action: str,
    expected: str,
    note: str = "",
    screenshot_size: tuple[int, int] | None = None,
) -> str:
    parts = [
        "You are analyzing a full macOS screenshot. Be exhaustive and precise.",
        "Split your answer into clearly labeled sections for mac_window and browser_window.",
        "Cover every visible interactive or semantically important object: buttons, icons, headers, titles, subtitles, descriptions, menus, tabs, inputs, radio buttons, checkboxes, dropdowns, dialogs, overlays, status text, and disabled controls.",
        "For each object, include: label/text, type/role, state, approximate pixel coordinates (center x/y, and bounding box if possible), and what the object can do.",
        "For web pages, also explain the page affordances: what the user can do here right now.",
        "Provide several action paths when possible: primary click path, keyboard path, and fallback/menu path.",
        "If something is uncertain, say so instead of inventing details.",
    ]
    if note:
        parts.append(f"Extra note: {note}")
    if screenshot_size:
        parts.append(
            f"Screenshot size: {screenshot_size[0]}x{screenshot_size[1]} pixels; use top-left origin coordinates."
        )
    parts.append(f"Action context: {action}")
    parts.append(f"Expected result: {expected}")
    parts.append(
        "Output in Markdown with these sections in this order: 1) summary, 2) mac_window, 3) browser_window, 4) visible_objects, 5) controls_by_type, 6) coordinates_map, 7) page_affordances, 8) recommended_actions, 9) blockers_or_risks, 10) verdict."
    )
    parts.append(
        "In controls_by_type, separate buttons, icons, inputs, radio buttons, checkboxes, dropdowns, and links."
    )
    parts.append(
        "In recommended_actions, give at least 2 concrete next steps and say exactly where to click or what to type."
    )
    parts.append(
        "Final line must be: VERDICT: PROCEED or VERDICT: RETRY or VERDICT: STOP."
    )
    return "\n".join(parts)


def run_vision_command(
    screenshot: Path, prompt: str, vision_cmd: str | None = None
) -> str:
    def _extract_text(stdout: str) -> str:
        parts: list[str] = []
        for line in stdout.splitlines():
            try:
                ev = json.loads(line)
                if ev.get("type") == "text":
                    parts.append(ev.get("part", {}).get("text", ""))
            except Exception:
                continue
        return "".join(parts).strip() or stdout.strip()

    def _status(text: str) -> str | None:
        upper = text.upper()
        for token in ("PROCEED", "RETRY", "STOP"):
            if token in upper:
                return token
        return None

    candidates: list[tuple[str, list[str] | str]] = []
    if vision_cmd or os.environ.get("FLOW_VISION_CMD"):
        template = vision_cmd or os.environ.get("FLOW_VISION_CMD") or ""
        if "{screenshot}" in template or "{prompt}" in template:
            candidates.append(("custom-template", template))
        else:
            candidates.append(
                (
                    "custom-template",
                    f"{template} --screenshot {{screenshot}} --prompt {{prompt}}",
                )
            )

    candidates.append(
        (
            "opencode-flash",
            [
                "opencode",
                "run",
                f"Image: {screenshot}. {prompt} Answer exactly with PROCEED, RETRY, or STOP. Use the Antigravity plugin model google/antigravity-gemini-3-flash directly; never use the direct Gemini API.",
                "--model",
                "google/antigravity-gemini-3-flash",
                "--format",
                "json",
            ],
        )
    )

    last_output = ""
    for name, candidate in candidates:
        try:
            if isinstance(candidate, str):
                rendered = candidate.format(
                    screenshot=shlex.quote(str(screenshot)),
                    prompt=shlex.quote(prompt),
                )
                proc = subprocess.run(
                    shlex.split(rendered), capture_output=True, text=True, check=False
                )
                raw = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
            else:
                proc = subprocess.run(
                    candidate, capture_output=True, text=True, check=False
                )
                raw = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")

            text = _extract_text(raw)
            last_output = text or raw.strip()
            status = _status(last_output)
            if status:
                return last_output
            if name == "look-screen" and last_output:
                return last_output
        except Exception as exc:
            last_output = f"{name} failed: {exc}"
            continue

    return last_output.strip()


def verdict_from_output(output: str) -> str:
    upper = output.upper()
    if "PROCEED" in upper:
        return "PROCEED"
    if "RETRY" in upper:
        return "RETRY"
    return "STOP"


def record_step(
    state: dict[str, Any],
    step_id: str,
    level: str,
    action: str,
    expected: str,
    note: str,
    screenshot: str,
    vision_output: str,
    verdict: str,
) -> dict[str, Any]:
    entry = {
        "id": step_id,
        "level": level,
        "action": action,
        "expected": expected,
        "note": note,
        "screenshot": screenshot,
        "vision_output": vision_output,
        "verdict": verdict,
        "timestamp": now(),
    }
    state["steps"].append(entry)
    return entry


def reset_incomplete_progress(state: dict[str, Any]) -> None:
    for level in LEVELS:
        state["progress"][level]["pair_buffer"] = 0
        state["progress"][level]["candidate_streak"] = 0


def feed_success(
    state: dict[str, Any], level_index: int = 0, promotions: list[str] | None = None
) -> list[str]:
    events = promotions if promotions is not None else []
    level = LEVELS[level_index]
    progress = state["progress"][level]
    progress["pair_buffer"] += 1
    if progress["pair_buffer"] < 2:
        events.append(f"{level}: pair buffer {progress['pair_buffer']}/2")
        return events

    progress["pair_buffer"] = 0
    progress["candidate_streak"] += 1
    events.append(f"{level}: candidate streak {progress['candidate_streak']}/10")

    if progress["candidate_streak"] < 10:
        return events

    progress["candidate_streak"] = 0
    progress["approved_units"] += 1
    events.append(f"{level}: approved units {progress['approved_units']}")

    if level == "full":
        progress["approved"] = True
        events.append("full: full-autorun approved")
        return events

    if progress["approved_units"] < 2:
        return events

    progress["approved_units"] = 0
    events.append(f"{level}: promoted to {LEVELS[level_index + 1]}")
    return feed_success(state, level_index + 1, events)


def rebuild_promotions(state: dict[str, Any]) -> list[str]:
    reset_incomplete_progress(state)
    events: list[str] = []
    for step in state.get("steps", []):
        if step.get("verdict") == "PROCEED":
            events = feed_success(state, 0, events)
        else:
            reset_incomplete_progress(state)
    return events


def flow_summary(state: dict[str, Any]) -> str:
    lines = []
    for level in LEVELS:
        progress = state["progress"][level]
        lines.append(
            f"{level}: pair={progress['pair_buffer']} candidate={progress['candidate_streak']} approved_units={progress['approved_units']} approved={progress['approved']}"
        )
    return "\n".join(lines)
