"""
Flask Merge Server — receives OS-level and browser-level events,
merges them chronologically, and writes a unified agent_workflow_master.json.

Endpoints:
  POST /os_log      — receives events from os_logger.py
  POST /browser_log — receives events from browser_logger.js
  GET  /status      — recording status and event count
  POST /stop        — finalize and flush the master JSON to disk
  GET  /events      — return the current merged event list
"""

from __future__ import annotations

import argparse
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS


class EventStore:
    def __init__(self, output_path: Path | None = None):
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._recording = True
        self._output_path = output_path

    def add_event(self, event: dict[str, Any]) -> None:
        with self._lock:
            self._events.append(event)

    def get_events(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._events)

    def stop_and_flush(self) -> dict[str, Any]:
        with self._lock:
            self._recording = False
            sorted_events = sorted(
                self._events,
                key=lambda e: e.get("timestamp", ""),
            )
            master = {
                "workflow": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "event_count": len(sorted_events),
                    "os_events": sum(
                        1 for e in sorted_events if e.get("source") == "os"
                    ),
                    "browser_events": sum(
                        1 for e in sorted_events if e.get("source") == "browser"
                    ),
                },
                "events": sorted_events,
            }
            if self._output_path:
                self._output_path.parent.mkdir(parents=True, exist_ok=True)
                self._output_path.write_text(
                    json.dumps(master, indent=2, ensure_ascii=False) + "\n"
                )
            self._events = sorted_events
            return master

    @property
    def recording(self) -> bool:
        return self._recording

    @property
    def event_count(self) -> int:
        with self._lock:
            return len(self._events)


def create_app(output_path: Path | None = None) -> Flask:
    app = Flask(__name__)
    CORS(app)
    store = EventStore(output_path=output_path)

    @app.route("/os_log", methods=["POST"])
    def os_log():
        event = request.get_json(force=True)
        store.add_event(event)
        return jsonify({"ok": True, "count": store.event_count})

    @app.route("/browser_log", methods=["POST"])
    def browser_log():
        event = request.get_json(force=True)
        store.add_event(event)
        return jsonify({"ok": True, "count": store.event_count})

    @app.route("/status", methods=["GET"])
    def status():
        return jsonify(
            {
                "recording": store.recording,
                "event_count": store.event_count,
                "output_path": str(store._output_path) if store._output_path else None,
            }
        )

    @app.route("/stop", methods=["POST"])
    def stop():
        master = store.stop_and_flush()
        return jsonify(
            {
                "ok": True,
                "event_count": master["workflow"]["event_count"],
                "output_path": str(store._output_path) if store._output_path else None,
            }
        )

    @app.route("/events", methods=["GET"])
    def events():
        return jsonify(store.get_events())

    return app


def main() -> int:
    parser = argparse.ArgumentParser(description="SIN-InkogniFlow Merge Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument(
        "--output", default="agent_workflow_master.json", help="Output JSON path"
    )
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    app = create_app(output_path=output_path)
    print(f"[agent_logger] Merge server → {args.host}:{args.port}")
    print(f"[agent_logger] Output → {output_path}")
    app.run(host=args.host, port=args.port, threaded=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
