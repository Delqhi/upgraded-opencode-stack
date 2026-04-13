"""
Execution Engine — replays a recorded workflow JSON with anti-bot countermeasures.

Modes:
  - cdp:       Browser actions via CDP selectors (nodriver)
  - pyautogui: Native app actions via pyautogui (absolute coordinates)
  - hybrid:    CDP for browser events, pyautogui for native app events (default)

Anti-bot features:
  - Bezier curve mouse movement (not linear — mimics human hand tremor)
  - Timestamp-based inter-event delays (preserves original human timing)
  - Random jitter on coordinates (+-2px) and delays (+-50ms)
  - Gaussian-distributed typing speed variation
  - Ghost-cursor-style mouse trail with overshoot on long distances
"""

from __future__ import annotations

import asyncio
import argparse
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any


def bezier_point(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    u = 1.0 - t
    return u**3 * p0 + 3 * u**2 * t * p1 + 3 * u * t**2 * p2 + t**3 * p3


def bezier_mouse_path(
    start: tuple[float, float],
    end: tuple[float, float],
    steps: int = 30,
    overshoot: bool = True,
) -> list[tuple[float, float]]:
    sx, sy = start
    ex, ey = end
    distance = math.hypot(ex - sx, ey - sy)

    perp_x = -(ey - sy) / max(distance, 1)
    perp_y = (ex - sx) / max(distance, 1)

    curvature = random.uniform(0.1, 0.35) * distance
    sign1 = random.choice([-1, 1])
    sign2 = random.choice([-1, 1])

    cp1_x = sx + (ex - sx) * 0.3 + perp_x * curvature * sign1
    cp1_y = sy + (ey - sy) * 0.3 + perp_y * curvature * sign1
    cp2_x = sx + (ex - sx) * 0.7 + perp_x * curvature * sign2
    cp2_y = sy + (ey - sy) * 0.7 + perp_y * curvature * sign2

    path: list[tuple[float, float]] = []
    for i in range(steps + 1):
        t = i / steps
        px = bezier_point(t, sx, cp1_x, cp2_x, ex)
        py = bezier_point(t, sy, cp1_y, cp2_y, ey)
        path.append((px, py))

    if overshoot and distance > 300:
        overshoot_factor = random.uniform(0.02, 0.06) * distance
        ox = ex + perp_x * overshoot_factor * sign1 * -1
        oy = ey + perp_y * overshoot_factor * sign1 * -1
        for i in range(1, 6):
            t_back = i / 5
            path.append(
                (
                    ox + (ex - ox) * t_back + random.uniform(-1, 1),
                    oy + (ey - oy) * t_back + random.uniform(-1, 1),
                )
            )

    jittered = []
    for px, py in path:
        jittered.append(
            (px + random.uniform(-0.5, 0.5), py + random.uniform(-0.5, 0.5))
        )
    return jittered


def jittered_delay(base_seconds: float) -> float:
    return max(0.0, base_seconds + random.gauss(0, min(0.05, base_seconds * 0.1)))


def jittered_coord(x: float, y: float, radius: float = 2.0) -> tuple[float, float]:
    return (x + random.uniform(-radius, radius), y + random.uniform(-radius, radius))


def compute_deltas(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    prev_ts: str | None = None
    for event in events:
        ts = event.get("timestamp", "")
        delta = 0.0
        if prev_ts and ts:
            try:
                from datetime import datetime, timezone

                t1 = datetime.fromisoformat(prev_ts)
                t2 = datetime.fromisoformat(ts)
                delta = (t2 - t1).total_seconds()
            except Exception:
                delta = 0.0
        delta = max(0.0, min(delta, 10.0))
        result.append({**event, "delta_seconds": delta})
        prev_ts = ts
    return result


async def replay_browser_event_cdp(event: dict[str, Any], tab: Any, dpr: float) -> None:
    import nodriver.cdp.input as input_cdp

    data = event.get("data", {})
    etype = event.get("type", "")
    elem = data.get("element", {})
    selector = elem.get("selector", "")

    if etype == "click":
        rect = elem.get("rect")
        if rect:
            x, y = jittered_coord(rect["x"] + rect["w"] / 2, rect["y"] + rect["h"] / 2)
            x_s, y_s = x / dpr, y / dpr
            path = bezier_mouse_path((0, 0), (x_s, y_s), steps=20)
            for px, py in path:
                await tab.send(input_cdp.dispatch_mouse_event("mouseMoved", x=px, y=py))
                await asyncio.sleep(0.008)
            await tab.send(
                input_cdp.dispatch_mouse_event(
                    "mousePressed",
                    x=x_s,
                    y=y_s,
                    button=input_cdp.MouseButton("left"),
                    buttons=1,
                    click_count=1,
                )
            )
            await asyncio.sleep(random.uniform(0.05, 0.12))
            await tab.send(
                input_cdp.dispatch_mouse_event(
                    "mouseReleased",
                    x=x_s,
                    y=y_s,
                    button=input_cdp.MouseButton("left"),
                    buttons=0,
                    click_count=1,
                )
            )
        elif selector:
            await tab.evaluate(f'document.querySelector("{selector}")?.click()')

    elif etype == "input":
        value = data.get("value", "")
        if selector and value:
            focused = await tab.evaluate(
                f'document.querySelector("{selector}") === document.activeElement'
            )
            if not focused:
                await tab.evaluate(f'document.querySelector("{selector}")?.focus()')
                await asyncio.sleep(0.05)
            for char in value:
                await tab.evaluate(
                    f'document.querySelector("{selector}").value += "{char}"'
                )
                await asyncio.sleep(max(0.02, random.gauss(0.08, 0.03)))

    elif etype == "change":
        value = data.get("value", "")
        if selector and value:
            await tab.evaluate(
                f'document.querySelector("{selector}").value = "{value}"; '
                f'document.querySelector("{selector}").dispatchEvent(new Event("change"))'
            )

    elif etype == "keydown":
        key = data.get("key", "")
        if key:
            await tab.send(input_cdp.dispatch_key_event("keyDown", key=key))
            await asyncio.sleep(random.uniform(0.03, 0.08))
            await tab.send(input_cdp.dispatch_key_event("keyUp", key=key))

    elif etype == "scroll":
        scroll_y = data.get("scrollY", 0)
        await tab.evaluate(f"window.scrollTo(0, {scroll_y})")
        await asyncio.sleep(0.1)

    elif etype == "navigation":
        url = data.get("url", "")
        if url:
            await tab.evaluate(f'window.location.href = "{url}"')
            await asyncio.sleep(0.5)

    elif etype == "submit":
        if selector:
            await tab.evaluate(f'document.querySelector("{selector}")?.submit()')

    elif etype == "focus":
        if selector:
            await tab.evaluate(f'document.querySelector("{selector}")?.focus()')


def replay_native_event_pyautogui(event: dict[str, Any]) -> None:
    import pyautogui

    pyautogui.PAUSE = 0.02
    pyautogui.FAILSAFE = True

    data = event.get("data", {})
    etype = event.get("type", "")

    if etype == "mouse_click":
        x, y = jittered_coord(float(data.get("x", 0)), float(data.get("y", 0)))
        current = pyautogui.position()
        path = bezier_mouse_path(
            (float(current[0]), float(current[1])), (x, y), steps=25
        )
        for px, py in path:
            pyautogui.moveTo(int(px), int(py), duration=0.008)
        button = data.get("button", "left")
        pyautogui.click(x=int(x), y=int(y), button=button)

    elif etype == "mouse_scroll":
        dx, dy = data.get("dx", 0), data.get("dy", 0)
        pyautogui.scroll(dy)

    elif etype == "key_press":
        key = data.get("key", "")
        if key and len(key) == 1:
            pyautogui.press(key)
        elif key:
            key_map = {
                "Key.space": "space",
                "Key.enter": "enter",
                "Key.tab": "tab",
                "Key.backspace": "backspace",
                "Key.esc": "escape",
            }
            mapped = key_map.get(key, key.lower().replace("key.", ""))
            try:
                pyautogui.press(mapped)
            except Exception:
                pass

    elif etype == "key_release":
        pass


async def run_hybrid(
    events: list[dict[str, Any]],
    cdp_port: int = 9335,
    speed: float = 1.0,
) -> None:
    import nodriver as uc

    events_with_deltas = compute_deltas(events)

    browser = await uc.start(
        browser_args=[f"--remote-debugging-port={cdp_port}"],
        headless=False,
    )
    tab = browser.main_tab
    dpr = await tab.evaluate("window.devicePixelRatio")

    for i, event in enumerate(events_with_deltas):
        delta = event["delta_seconds"] / speed
        await asyncio.sleep(jittered_delay(delta))

        source = event.get("source", "")
        etype = event.get("type", "")

        if etype in (
            "recording_start",
            "recording_stop",
            "mouse_position",
            "window_focus",
        ):
            continue

        if source == "browser":
            await replay_browser_event_cdp(event, tab, dpr)
        elif source == "os":
            window = event.get("active_window", {})
            bundle = window.get("bundle_id", "")
            if bundle and "chrome" in bundle.lower():
                await replay_browser_event_cdp(event, tab, dpr)
            else:
                replay_native_event_pyautogui(event)

        print(f"[{i + 1}/{len(events_with_deltas)}] {source}/{etype} (Δ{delta:.2f}s)")

    await asyncio.sleep(1)


def run_cdp_only(
    events: list[dict[str, Any]], cdp_port: int = 9335, speed: float = 1.0
) -> None:
    browser_events = [e for e in events if e.get("source") == "browser"]
    asyncio.run(run_hybrid(browser_events, cdp_port=cdp_port, speed=speed))


def run_pyautogui_only(events: list[dict[str, Any]], speed: float = 1.0) -> None:
    events_with_deltas = compute_deltas(events)
    for i, event in enumerate(events_with_deltas):
        delta = event["delta_seconds"] / speed
        time.sleep(jittered_delay(delta))
        etype = event.get("type", "")
        if etype in (
            "recording_start",
            "recording_stop",
            "mouse_position",
            "window_focus",
        ):
            continue
        replay_native_event_pyautogui(event)
        print(f"[{i + 1}/{len(events_with_deltas)}] os/{etype} (Δ{delta:.2f}s)")


def main() -> int:
    parser = argparse.ArgumentParser(description="SIN-InkogniFlow Workflow Executor")
    parser.add_argument(
        "--workflow", required=True, help="Path to agent_workflow_master.json"
    )
    parser.add_argument(
        "--mode",
        default="hybrid",
        choices=["cdp", "pyautogui", "hybrid"],
        help="Execution mode (default: hybrid)",
    )
    parser.add_argument(
        "--cdp-port", type=int, default=9335, help="CDP port for nodriver"
    )
    parser.add_argument(
        "--speed", type=float, default=1.0, help="Playback speed multiplier"
    )
    parser.add_argument(
        "--filter-type", default=None, help="Only replay events matching this type"
    )
    args = parser.parse_args()

    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        print(f"Error: {workflow_path} not found")
        return 1

    data = json.loads(workflow_path.read_text())
    events = data.get("events", [])

    if args.filter_type:
        events = [e for e in events if e.get("type") == args.filter_type]

    if not events:
        print("No events to replay")
        return 0

    print(f"Replaying {len(events)} events in {args.mode} mode (speed={args.speed}x)")

    if args.mode == "cdp":
        run_cdp_only(events, cdp_port=args.cdp_port, speed=args.speed)
    elif args.mode == "pyautogui":
        run_pyautogui_only(events, speed=args.speed)
    else:
        asyncio.run(run_hybrid(events, cdp_port=args.cdp_port, speed=args.speed))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
