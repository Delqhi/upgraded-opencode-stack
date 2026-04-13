#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from sin_flow_runtime import (
    archive_flow,
    create_flow_workspace,
    rebuild_flow_brain,
    run_flow_step,
    run_keyshot,
    status_text,
)
from _flow_common import ensure_state, resolve_root, slugify


class FlowAPI(BaseHTTPRequestHandler):
    root_arg = None

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode()
        return json.loads(raw) if raw.strip() else {}

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/health":
            return self._send(200, {"ok": True})
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 3 and parts[0] == "v1" and parts[1] == "flows":
            flow = parts[2]
            if len(parts) == 4 and parts[3] == "status":
                create_flow_workspace(flow, self.root_arg)
                return self._send(200, {"flow": flow, "status": status_text(flow, root_arg=self.root_arg)})
            if len(parts) == 4 and parts[3] == "state":
                root = resolve_root(self.root_arg)
                slug = slugify(flow)
                state = ensure_state(flow, slug, root)
                return self._send(200, {"flow": flow, "state": state})
        return self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        parts = [p for p in path.split("/") if p]
        body = self._read_json()

        if path == "/v1/flows":
            flow = body.get("flow") or body.get("name")
            if not flow:
                return self._send(400, {"error": "missing_flow"})
            result = create_flow_workspace(flow, body.get("root") or self.root_arg, body.get("description", ""))
            return self._send(200, {"flow": flow, "slug": result["slug"], "root": result["root"], "state": result["state"]})

        if len(parts) >= 3 and parts[0] == "v1" and parts[1] == "flows":
            flow = parts[2]
            if len(parts) == 4 and parts[3] == "step":
                result = run_flow_step(
                    flow,
                    action=body.get("action", ""),
                    expected=body.get("expected", "action succeeded"),
                    note=body.get("note", ""),
                    root_arg=body.get("root") or self.root_arg,
                    mode=body.get("mode", "auto"),
                    level=body.get("level", "run"),
                    vision_cmd=body.get("vision_cmd"),
                    dry_run=bool(body.get("dry_run", False)),
                )
                return self._send(200, result)

            if len(parts) == 4 and parts[3] == "keyshot":
                result = run_keyshot(
                    flow,
                    expected=body.get("expected", "screen state matches"),
                    note=body.get("note", ""),
                    root_arg=body.get("root") or self.root_arg,
                    vision_cmd=body.get("vision_cmd"),
                    level=body.get("level", "run"),
                )
                return self._send(200, result)

            if len(parts) == 4 and parts[3] == "brain":
                result = rebuild_flow_brain(flow, root_arg=body.get("root") or self.root_arg)
                return self._send(200, result)

            if len(parts) == 4 and parts[3] == "archive":
                result = archive_flow(flow, root_arg=body.get("root") or self.root_arg)
                return self._send(200, result)

        return self._send(404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        return


def main() -> int:
    parser = argparse.ArgumentParser(prog="sin-flowd", description="Fast flow API daemon")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--root", default=None)
    args = parser.parse_args()
    FlowAPI.root_arg = args.root
    server = ThreadingHTTPServer((args.host, args.port), FlowAPI)
    print(f"[sin-flowd] listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
