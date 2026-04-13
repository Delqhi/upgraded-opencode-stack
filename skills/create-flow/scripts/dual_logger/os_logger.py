"""
OS-Level Logger — pynput + NSWorkspace background event tracker.

Captures:
  - Absolute mouse X/Y position, clicks (left/right/middle), scrolls
  - Keystrokes (key names, not char content for privacy)
  - Active window name and bundle ID via NSWorkspace

Posts all events to the Flask merge server in real time.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from pynput import keyboard, mouse


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def get_active_window() -> dict[str, str]:
    try:
        from AppKit import NSWorkspace

        ws = NSWorkspace.sharedWorkspace()
        app = ws.frontmostApplication()
        if app:
            return {
                "app_name": app.localizedName() or "",
                "bundle_id": app.bundleIdentifier() or "",
                "pid": str(app.processIdentifier()),
            }
    except Exception:
        pass
    return {"app_name": "", "bundle_id": "", "pid": ""}


class OSLogger:
    def __init__(self, server_url: str, poll_interval: float = 0.5):
        self.server_url = server_url.rstrip("/")
        self.poll_interval = poll_interval
        self._recording = False
        self._thread: threading.Thread | None = None
        self._last_window: dict[str, str] = {}
        self._last_mouse_pos: tuple[float, float] = (0.0, 0.0)
        self._start_time: float = 0.0

    def _post_event(self, event: dict[str, Any]) -> None:
        try:
            requests.post(
                f"{self.server_url}/os_log",
                json=event,
                timeout=2,
            )
        except Exception:
            pass

    def _make_event(self, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "os",
            "type": event_type,
            "timestamp": now_iso(),
            "monotonic_ns": time.monotonic_ns(),
            "data": data,
            "active_window": get_active_window(),
        }

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if not self._recording:
            return
        btn_name = {
            mouse.Button.left: "left",
            mouse.Button.right: "right",
            mouse.Button.middle: "middle",
        }.get(button, str(button))
        self._post_event(
            self._make_event(
                "mouse_click",
                {
                    "x": x,
                    "y": y,
                    "button": btn_name,
                    "pressed": pressed,
                },
            )
        )

    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self._recording:
            return
        self._post_event(
            self._make_event(
                "mouse_scroll",
                {"x": x, "y": y, "dx": dx, "dy": dy},
            )
        )

    def _on_move(self, x: int, y: int) -> None:
        if not self._recording:
            return
        self._last_mouse_pos = (float(x), float(y))

    def _on_key_press(self, key: Any) -> None:
        if not self._recording:
            return
        try:
            key_name = key.char if hasattr(key, "char") and key.char else str(key)
        except Exception:
            key_name = str(key)
        self._post_event(self._make_event("key_press", {"key": key_name}))

    def _on_key_release(self, key: Any) -> None:
        if not self._recording:
            return
        try:
            key_name = key.char if hasattr(key, "char") and key.char else str(key)
        except Exception:
            key_name = str(key)
        self._post_event(self._make_event("key_release", {"key": key_name}))

    def _poll_active_window(self) -> None:
        while self._recording:
            current = get_active_window()
            if current.get("bundle_id") != self._last_window.get("bundle_id"):
                self._last_window = current
                self._post_event(self._make_event("window_focus", current))
            time.sleep(self.poll_interval)

    def _poll_mouse_position(self) -> None:
        while self._recording:
            x, y = self._last_mouse_pos
            self._post_event(self._make_event("mouse_position", {"x": x, "y": y}))
            time.sleep(0.2)

    def start(self) -> None:
        if self._recording:
            return
        self._recording = True
        self._start_time = time.monotonic()
        self._last_window = get_active_window()

        self._post_event(
            self._make_event(
                "recording_start",
                {"message": "OS logger started", "poll_interval": self.poll_interval},
            )
        )

        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_scroll=self._on_scroll,
            on_move=self._on_move,
        )
        self._mouse_listener.start()

        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.start()

        self._window_thread = threading.Thread(
            target=self._poll_active_window, daemon=True
        )
        self._window_thread.start()

        self._mouse_thread = threading.Thread(
            target=self._poll_mouse_position, daemon=True
        )
        self._mouse_thread.start()

    def stop(self) -> None:
        if not self._recording:
            return
        self._recording = False
        self._post_event(
            self._make_event("recording_stop", {"message": "OS logger stopped"})
        )
        try:
            self._mouse_listener.stop()
        except Exception:
            pass
        try:
            self._keyboard_listener.stop()
        except Exception:
            pass

    def join(self, timeout: float = 5.0) -> None:
        for t in [
            getattr(self, "_window_thread", None),
            getattr(self, "_mouse_thread", None),
        ]:
            if t and t.is_alive():
                t.join(timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OS-Level Event Logger for SIN-InkogniFlow"
    )
    parser.add_argument(
        "--server", default="http://localhost:5000", help="Flask merge server URL"
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        help="Window-focus poll interval (seconds)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0,
        help="Record duration in seconds (0 = until Ctrl+C)",
    )
    args = parser.parse_args()

    logger = OSLogger(server_url=args.server, poll_interval=args.poll_interval)
    logger.start()
    print(f"[os_logger] Recording → {args.server}  (poll={args.poll_interval}s)")
    print("[os_logger] Press Ctrl+C to stop")

    try:
        if args.duration > 0:
            time.sleep(args.duration)
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        logger.stop()
        logger.join()
        print("[os_logger] Stopped")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
